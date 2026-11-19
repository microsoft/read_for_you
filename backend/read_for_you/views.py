import os
import json
import logging
import time
import base64
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse, HttpResponse
from django.conf import settings
from .Services.PDFService import PDFService
from .Services.ProcessingService import ProcessingService
from .Services.RecognitionServices import RecognitionServices
from .Services.AzureBlobService import AzureBlobService
from .Services.AzureBlobService2 import AzureBlobService2
from .Services.SqlService import SqlService
from .Services.test import testBulkJSON
import asyncio

logger = logging.getLogger(__name__)

# 在线书库允许下载的文件类型
LIBRARY_FILE_TYPES = {'pdf', 'json'}

def _standard_api_response(success: bool, data=None, error_msg: str = "") -> JsonResponse:
	"""统一结构的 JSON 响应，HTTP 状态码固定为 200"""
	return JsonResponse({
		"status": "success" if success else "failed",
		"data": data,
		"error_msg": error_msg,
	}, status=200)

@csrf_exempt
def recognition(request):
	"""
	识别路由：处理PDF文件上传并进行异步识别
	1. 调用 PDFService.extractPDF 裁剪 PDF
	2. 调用异步API拿到request_id
	3. 添加数据库数据，存入uuid(cookie), bookName, pageRange, request_id等信息
	4. 循环调用checkStatus，直到状态为complete或error时返回json_response
	"""
	# 1. 解析请求参数
	file = request.FILES.get('file')
	page_range = request.POST.get('pageNum', '')
	language = request.GET.get('language', '')
	book_name = request.POST.get('bookName', file.name if file else 'unknown')

	# 获取用户 ID
	user_id = request.COOKIES.get('rfy_uuid', '')
	if not user_id:
		return _standard_api_response(False, error_msg='未找到用户 ID')

	if not file:
		return _standard_api_response(False, error_msg='缺少文件参数')

	if file.size > settings.MAX_UPLOAD_BYTES:
		return _standard_api_response(False, error_msg='文件过大')

	book_name = book_name[:255]

	try:
		# 2. 使用 PDFService 裁剪 PDF
		extracted_pdf = PDFService.extractPDF(file, page_range)
		file_data = extracted_pdf.read()

		# 将页码范围转换为从1开始（用于传给识别 API）
		normalized_page_range = ''
		if page_range:
			normalized_page_range = PDFService.normalizePageRange(page_range)

		# 3. 调用异步识别 API 获取 request_id
		request_id = RecognitionServices.callAsyncRecognitionAPI(file_data, normalized_page_range, language)

		if not request_id:
			return _standard_api_response(False, error_msg='调用异步识别 API 失败')

		# 4. 插入数据库记录
		sql_service = SqlService()
		insert_result = sql_service.insert_task(
			user_id=user_id,
			request_id=request_id,
			book_name=book_name,
			page_range=page_range,
			status='Running'
		)

		if not insert_result['success']:
			logger.warning("数据库插入失败: %s", insert_result['error_msg'])

		# 5. 轮询 checkStatus 直到完成或出错
		max_retries = 30  # 最多轮询 30 次
		poll_interval = 5  # 每次间隔 5 秒

		for _ in range(max_retries):
			status_result = RecognitionServices.checkStatus(request_id)
			status = status_result.get('status')

			if status == 'success':
				# 更新数据库状态为 completed
				sql_service.update_task_status(request_id, 'Completed')

				# 将 PDF 转换为 base64 格式
				pdf_base64 = base64.b64encode(file_data).decode('utf-8')
				pdf_data_url = f'data:application/pdf;base64,{pdf_base64}'

				# 上传 PDF 和结果 JSON 到 Azure Blob Storage
				# 从 request_id 中提取最后的随机字符串部分
				request_id_suffix = request_id.rstrip('/').split('/')[-1]
				upload_prefix = f"results_of_users/{request_id_suffix}"

				blob_service = AzureBlobService()

				# 上传 PDF 文件
				pdf_file = BytesIO(file_data)
				pdf_file.name = "result.pdf"
				blob_service.uploadFile(upload_prefix, pdf_file)

				# 上传结果 JSON 文件
				result_data = status_result.get('result')
				result_json_bytes = json.dumps(result_data, ensure_ascii=False, indent=2).encode('utf-8')
				json_file = BytesIO(result_json_bytes)
				json_file.name = "result.json"
				blob_service.uploadFile(upload_prefix, json_file)

				# 返回与以前相同的 JSON 格式
				return JsonResponse({
					'status': 'success',
					'result': result_data,
					'pdf': pdf_data_url
				})

			elif status == 'error':
				# 更新数据库状态为 error
				sql_service.update_task_status(request_id, 'error')
				logger.warning("识别出错: %s", status_result.get('error_message'))
				return _standard_api_response(False, error_msg='识别出错')

			elif status == 'Running':
				# 继续等待
				time.sleep(poll_interval)
			else:
				# 未知状态
				sql_service.update_task_status(request_id, 'error')
				logger.warning("识别返回未知状态: %s", status)
				return _standard_api_response(False, error_msg='识别出错')

		# 超时
		sql_service.update_task_status(request_id, 'timeout')
		return _standard_api_response(False, error_msg='识别超时')

	except Exception:
		logger.exception("recognition 失败")
		return _standard_api_response(False, error_msg='识别过程中发生错误')



@csrf_exempt
def getStoragedData(request):
	"""
	从 Azure Blob Storage 获取在线书库里某本书的文件

	参数:
		prefix: 书的 book_prefix，必须出现在 metadata/books_list.json 里
		type: 文件类型，pdf 或 json

	返回:
		如果是 PDF: JSON 格式的 PDF base64 数组
		如果是 JSON: 解析后的 JSON
	"""
	try:
		# 1. 解析请求参数
		prefix = request.GET.get('prefix', '').strip().rstrip('/')
		file_type = request.GET.get('type', '').lower()

		if file_type not in LIBRARY_FILE_TYPES:
			return JsonResponse({'error': '不支持的文件类型'}, status=400)

		# 2. 只允许读取在线书库里的书，不能读取用户上传的结果等其他文件
		blob_service = AzureBlobService()
		if not prefix or prefix not in blob_service.get_library_prefixes():
			return JsonResponse({'error': '文件不存在'}, status=404)

		file_data = blob_service.downloadFile(prefix + '/', file_type)

		# 3. 根据文件类型返回数据
		if file_type == 'pdf':
			# PDF 文件：转换为 base64 返回
			pdf_base64 = base64.b64encode(file_data).decode('utf-8')
			return JsonResponse({
				'type': 'pdf',
				'data': f'data:application/pdf;base64,{pdf_base64}'
			})
		else:
			# JSON 文件：解析后返回
			json_data = json.loads(file_data.decode('utf-8'))
			return JsonResponse({
				'type': 'json',
				'data': json_data
			})

	except FileNotFoundError:
		return JsonResponse({'error': '文件不存在'}, status=404)
	except Exception:
		logger.exception("getStoragedData 失败")
		return JsonResponse({'error': '获取文件失败'}, status=500)


@csrf_exempt
def getBookMetadata(request):
	blob_service=AzureBlobService()
	try:
		metadata=blob_service.download_meta_data()
		return JsonResponse(metadata)
	except Exception:
		logger.exception("获取书籍元数据失败")
		return JsonResponse({
			'success': False,
			'error': '获取书籍元数据失败'
		}, status=500)


@csrf_exempt
def getImageFromAB2(request):
	if request.method != 'POST':
		return _standard_api_response(False, error_msg='仅支持 POST 请求')

	try:
		payload = json.loads(request.body.decode('utf-8') or '{}')
		image_url = payload.get('imageUrl') or payload.get('image_url')
	except json.JSONDecodeError:
		return _standard_api_response(False, error_msg='请求体不是有效的 JSON')

	if not image_url:
		return _standard_api_response(False, error_msg='缺少参数 imageUrl')

	try:
		blob_service = AzureBlobService2()
		data_url = blob_service.downloadImageAsBase64(image_url)
		return _standard_api_response(True, data=data_url)
	except Exception:
		logger.exception("getImageFromAB2 失败")
		return _standard_api_response(False, error_msg='获取图片失败')


@csrf_exempt
def getBookHistory(request):
	"""
	获取用户历史记录
	"""
	# 1. 获取用户 ID
	user_id = request.COOKIES.get('rfy_uuid')
	if not user_id:
		return _standard_api_response(False, error_msg='未找到用户 ID')

	# 2. 调用 SqlService 获取数据
	try:
		sql_service = SqlService()
		result = sql_service.get_tasks_by_user_id(user_id)
		
		if result['success']:
			return _standard_api_response(True, data=result['data'])
		else:
			return _standard_api_response(False, error_msg='获取历史记录失败')

	except Exception:
		logger.exception("getBookHistory 失败")
		return _standard_api_response(False, error_msg='获取历史记录失败')


@csrf_exempt
def getResultOfUser(request):
	"""
	根据 request_id 获取用户的识别结果（只能取自己的）
	POST: { "request_id": "/api/intelligentOcr/analyzeResults/abc123xyz" }
	返回: { "json": <识别结果>, "pdf": "data:application/pdf;base64,..." }
	"""
	if request.method != 'POST':
		return _standard_api_response(False, error_msg='仅支持 POST 请求')

	user_id = request.COOKIES.get('rfy_uuid')
	if not user_id:
		return _standard_api_response(False, error_msg='未找到用户 ID')

	try:
		payload = json.loads(request.body.decode('utf-8') or '{}')
		request_id = payload.get('request_id', '')
	except json.JSONDecodeError:
		return _standard_api_response(False, error_msg='请求体不是有效的 JSON')

	if not request_id or not isinstance(request_id, str):
		return _standard_api_response(False, error_msg='缺少参数 request_id')

	# 只允许读取当前用户自己提交的任务
	if not SqlService().task_belongs_to_user(user_id, request_id):
		return _standard_api_response(False, error_msg='文件不存在')

	# 从 request_id 中提取最后的随机字符串部分
	request_id_suffix = request_id.rstrip('/').split('/')[-1]
	prefix = f"results_of_users/{request_id_suffix}"

	try:
		blob_service = AzureBlobService()

		# 下载 PDF 文件
		pdf_data = blob_service.downloadFile(prefix, 'pdf')
		pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
		pdf_data_url = f'data:application/pdf;base64,{pdf_base64}'

		# 下载 JSON 文件
		json_data = blob_service.downloadFile(prefix, 'json')
		result_json = json.loads(json_data.decode('utf-8'))

		# 返回与 recognition 相同的 JSON 格式
		return JsonResponse({
			'status': 'success',
			'result': result_json,
			'pdf': pdf_data_url
		})

	except FileNotFoundError:
		return _standard_api_response(False, error_msg='文件不存在')
	except Exception:
		logger.exception("getResultOfUser 失败")
		return _standard_api_response(False, error_msg='获取结果失败')
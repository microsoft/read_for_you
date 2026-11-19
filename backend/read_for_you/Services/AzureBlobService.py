import os
import traceback
from typing import List, Dict, Union
from azure.storage.blob import BlobServiceClient, BlobClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from io import BytesIO
import asyncio
from ..constants import (
	AZURE_STORAGE_CONNECTION_STRING,
	AZURE_STORAGE_CONTAINER_NAME,
	AZURE_STORAGE_ACCOUNT_NAME,
	AZURE_STORAGE_ACCOUNT_KEY,
)


class AzureBlobService:
	"""Azure Blob Storage 服务类"""

	def __init__(self):
		"""初始化 Azure Blob Storage 客户端"""
		# 下载优化参数
		self.download_concurrency = 8
		self.max_chunk_get_size = 32 * 1024 * 1024
		self.max_single_get_size = 1024 * 1024 * 1024
		connection_string = AZURE_STORAGE_CONNECTION_STRING
		if not connection_string:
			raise ValueError("AZURE_STORAGE_CONNECTION_STRING 未配置，请在 constants.py 中设置")
		self.connection_string = connection_string
		self.blob_service_client = BlobServiceClient.from_connection_string(
		    connection_string)
		self.container_name = AZURE_STORAGE_CONTAINER_NAME
		if not self.container_name:
			raise ValueError("AZURE_STORAGE_CONTAINER_NAME 未配置，请在 constants.py 中设置")

	def _generate_blob_url_with_sas(self, blob_name: str, expiry_hours: int = 24) -> str:
		"""生成带 SAS Token 的 Blob 访问 URL，默认有效期 24 小时。"""
		try:
			if AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY:
				sas_token = generate_blob_sas(
					account_name=AZURE_STORAGE_ACCOUNT_NAME,
					container_name=self.container_name,
					blob_name=blob_name,
					account_key=AZURE_STORAGE_ACCOUNT_KEY,
					permission=BlobSasPermissions(read=True),
					expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
				)
				return f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
			# 如果缺少账号信息，退化为直接返回公开 URL
			container_client = self.blob_service_client.get_container_client(
			    self.container_name)
			blob_client = container_client.get_blob_client(blob_name)
			return blob_client.url
		except Exception:
			# 如果生成失败，返回普通 URL 以保证功能可用
			container_client = self.blob_service_client.get_container_client(
			    self.container_name)
			return container_client.get_blob_client(blob_name).url

	def downloadFile(self, prefix: str, file_type: str) -> Union[bytes, List[str]]:
		try:
			container_client = self.blob_service_client.get_container_client(
				self.container_name)
			blob_list = container_client.list_blobs(name_starts_with=prefix)

			for blob in blob_list:
				blob_name = blob.name

				if blob_name.lower().endswith(file_type.lower()):
					blob_client = BlobClient.from_connection_string(
						conn_str=self.connection_string,
						container_name=self.container_name,
						blob_name=blob_name,
						max_single_get_size=self.max_single_get_size,
						max_chunk_get_size=self.max_chunk_get_size,
					)
					# 仅 max_concurrency 可以放在 download_blob()
					download_stream = blob_client.download_blob(
						max_concurrency=self.download_concurrency
					)

					chunks = []
					try:
						for chunk in download_stream.chunks():
							chunks.append(chunk)
						file_data = b''.join(chunks)
					finally:
						del download_stream
						del chunks

					return file_data

			raise FileNotFoundError(f"未找到符合条件的文件: prefix='{prefix}', type='{file_type}'")

		except Exception as e:
			print(f"❌ downloadFile Error:")
			print(f"   错误类型: {type(e).__name__}")
			print(f"   错误信息: {e}")
			raise

	def _load_books_list(self) -> list:
		container_client = self.blob_service_client.get_container_client(self.container_name)
		blob_client = container_client.get_blob_client('metadata/books_list.json')
		file_data = blob_client.download_blob().readall()

		import json
		return json.loads(file_data.decode('utf-8'))

	def get_library_prefixes(self) -> set:
		"""在线书库中允许公开读取的 book_prefix 集合（统一不带结尾的 /）"""
		return {
			book['book_prefix'].rstrip('/')
			for book in self._load_books_list()
			if book.get('book_prefix')
		}

	def download_meta_data(self):
		"""
		下载书籍元数据，并为每本书注入带 SAS Token 的封面图片 URL。
		
		返回格式:
		{
			'success': True,
			'count': <书籍数量>,
			'data': [
				{
					'book_id': '0',
					'book_prefix': 'zbooksnap/0/',
					'cover_file': 'cover.jpg',
					'imageUrl': 'https://...blob.core.windows.net/container/zbooksnap/0/cover.jpg?sas_token',
					...其他字段
				},
				...
			]
		}
		"""
		books_metadata = self._load_books_list()

		# 为每本书注入带 SAS Token 的封面图片 URL
		for book in books_metadata:
			book_prefix = book.get('book_prefix', '')
			cover_file = book.get('cover_file', '')
			if book_prefix and cover_file:
				# 拼接 blob 路径: book_prefix + cover_file
				blob_name = book_prefix.rstrip('/') + '/' + cover_file
				# 生成带 SAS 的完整 URL
				book['imageUrl'] = self._generate_blob_url_with_sas(blob_name)
			else:
				book['imageUrl'] = ''

		return {
			'success': True,
			'count': len(books_metadata),
			'data': books_metadata
		}

	# def downloadFile(self, info):
	# 	"""
	# 	根据 info 字典下载文件并返回统一格式的 JSON。
	# 	info 字段: userId, bookName, index, type
	# 	返回: {"status": "success"|"failed", "data": <base64 or parsed content>, "error_msg": ""}
	# 	"""
	# 	try:
	# 		blob_name = "/".join([info["userId"], info["bookName"], str(info["index"]), info["type"]])
	# 		blob_client = BlobClient.from_connection_string(
	# 			conn_str=self.connection_string,
	# 			container_name=self.container_name,
	# 			blob_name=blob_name,
	# 			max_single_get_size=self.max_single_get_size,
	# 			max_chunk_get_size=self.max_chunk_get_size,
	# 		)
			
	# 		download_stream = blob_client.download_blob(
	# 			max_concurrency=self.download_concurrency
	# 		)
			
	# 		chunks = []
	# 		try:
	# 			for chunk in download_stream.chunks():
	# 				chunks.append(chunk)
	# 			file_data = b''.join(chunks)
	# 		finally:
	# 			del download_stream
	# 			del chunks
			
	# 		# 根据文件类型决定返回格式
	# 		file_type = info["type"].lower()
	# 		if file_type == "pdf":
	# 			import base64
	# 			pdf_base64 = base64.b64encode(file_data).decode('utf-8')
	# 			return {
	# 				"status": "success",
	# 				"data": f"data:application/pdf;base64,{pdf_base64}",
	# 				"error_msg": ""
	# 			}
	# 		elif file_type == "json":
	# 			import json
	# 			json_data = json.loads(file_data.decode('utf-8'))
	# 			return {
	# 				"status": "success",
	# 				"data": json_data,
	# 				"error_msg": ""
	# 			}
	# 		else:
	# 			# 其他文件返回 base64
	# 			import base64
	# 			file_base64 = base64.b64encode(file_data).decode('utf-8')
	# 			return {
	# 				"status": "success",
	# 				"data": file_base64,
	# 				"error_msg": ""
	# 			}
		
	# 	except FileNotFoundError:
	# 		return {
	# 			"status": "failed",
	# 			"data": None,
	# 			"error_msg": f"文件不存在: {blob_name}"
	# 		}
	# 	except Exception as e:
	# 		return {
	# 			"status": "failed",
	# 			"data": None,
	# 			"error_msg": f"下载文件失败: {e}"
	# 		}

	def uploadFile(self, prefix: str, file) -> bool:
		"""
		上传文件到 Azure Blob Storage

		参数:
			prefix: 上传文件夹路径前缀，如 "user123/books/"
			file: 上传的文件对象（Django UploadedFile 或类似对象，需有 name 和 read() 方法）

		返回:
			bool: 上传成功返回 True，失败返回 False
		"""
		try:
			# 获取文件名
			file_name = getattr(file, 'name', 'unknown_file')
			
			# 拼接完整的 blob 路径
			blob_name = prefix.rstrip('/') + '/' + file_name
			
			# 读取文件数据
			if hasattr(file, 'read'):
				file_data = file.read()
				# 重置文件指针（如果需要再次读取）
				if hasattr(file, 'seek'):
					file.seek(0)
			else:
				# 如果是 bytes 类型
				file_data = file
			
			# 获取 blob client
			container_client = self.blob_service_client.get_container_client(self.container_name)
			blob_client = container_client.get_blob_client(blob_name)
			
			# 上传文件
			blob_client.upload_blob(file_data, overwrite=True)
			
			print(f"✅ 文件上传成功: {blob_name}")
			return True

		except Exception as e:
			print(f"❌ uploadFile Error:")
			print(f"   错误类型: {type(e).__name__}")
			print(f"   错误信息: {e}")
			return False
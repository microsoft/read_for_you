from pypdf import PdfReader, PdfWriter
from io import BytesIO


class PDFService:
	"""PDF处理服务类"""

	@staticmethod
	def extractPDF(file, pageRange):
		"""
		根据页码范围提取PDF页面

		参数:
			file: 上传的PDF文件对象
			pageRange: 页码范围字符串，格式如 "1-3" 或 "1,3,5" 或 "1-3,5,7-9"

		返回:
			BytesIO: 包含提取页面的PDF文件对象
		"""
		try:
			# 读取上传的PDF文件
			pdf_reader = PdfReader(file)
			pdf_writer = PdfWriter()

			# 解析页码范围
			page_indices = PDFService._parse_page_range(
				pageRange, len(pdf_reader.pages))

			# 提取指定页面
			for page_index in page_indices:
				if 0 <= page_index < len(pdf_reader.pages):
					pdf_writer.add_page(pdf_reader.pages[page_index])

			# 将提取的页面写入BytesIO对象
			output = BytesIO()
			pdf_writer.write(output)
			output.seek(0)  # 重置指针到文件开头

			return output

		except Exception as e:
			raise Exception(f"PDF提取失败: {str(e)}")

	@staticmethod
	def normalizePageRange(pageRange):
		"""
		将页码范围平移到从1开始

		参数:
			pageRange: 原始页码范围字符串，如 "3-6" 或 "7-7" 或 "5,7,9" 或 "3-6,8-10"

		返回:
			str: 转换后的页码范围字符串，如 "1-4" 或 "1-1" 或 "1,3,5" 或 "1-4,6-8"
		"""
		if not pageRange:
			return ""

		try:
			# 解析所有页码
			page_numbers = set()
			ranges = pageRange.split(',')

			for r in ranges:
				r = r.strip()
				if '-' in r:
					# 处理范围，如 "3-6"
					start, end = r.split('-')
					start = int(start.strip())
					end = int(end.strip())
					page_numbers.update(range(start, end + 1))
				else:
					# 处理单个页码，如 "5"
					page_num = int(r.strip())
					page_numbers.add(page_num)

			if not page_numbers:
				return ""

			# 排序页码
			sorted_pages = sorted(list(page_numbers))
			min_page = sorted_pages[0]

			# 平移页码，使最小页码变为1
			normalized_pages = [p - min_page + 1 for p in sorted_pages]

			# 将页码列表转换回范围字符串
			return PDFService._pages_to_range_string(normalized_pages)

		except Exception as e:
			raise Exception(f"页码范围转换失败: {str(e)}")

	@staticmethod
	def _pages_to_range_string(pages):
		"""
		将页码列表转换为范围字符串

		参数:
			pages: 排序后的页码列表，如 [1, 2, 3, 5, 7, 8, 9]

		返回:
			str: 范围字符串，如 "1-3,5,7-9"
		"""
		if not pages:
			return ""

		ranges = []
		start = pages[0]
		end = pages[0]

		for i in range(1, len(pages)):
			if pages[i] == end + 1:
				# 连续页码，扩展范围
				end = pages[i]
			else:
				# 不连续，保存当前范围并开始新范围
				if start == end:
					ranges.append(str(start))
				else:
					ranges.append(f"{start}-{end}")
				start = pages[i]
				end = pages[i]

		# 添加最后一个范围
		if start == end:
			ranges.append(str(start))
		else:
			ranges.append(f"{start}-{end}")

		return ','.join(ranges)

	@staticmethod
	def _parse_page_range(pageRange, total_pages):
		"""
		解析页码范围字符串

		参数:
			pageRange: 页码范围字符串，如 "1-3" 或 "1,3,5" 或 "1-3,5,7-9"
			total_pages: PDF总页数

		返回:
			list: 页码索引列表（从0开始）
		"""
		if not pageRange:
			# 如果没有指定范围，返回所有页面
			return list(range(total_pages))

		page_indices = set()
		ranges = pageRange.split(',')

		for r in ranges:
			r = r.strip()
			if '-' in r:
				# 处理范围，如 "1-3"
				start, end = r.split('-')
				start = int(start.strip())
				end = int(end.strip())
				# 转换为0-based索引
				page_indices.update(range(start - 1, end))
			else:
				# 处理单个页码，如 "5"
				page_num = int(r.strip())
				# 转换为0-based索引
				page_indices.add(page_num - 1)

		# 返回排序后的页码列表
		return sorted(list(page_indices))

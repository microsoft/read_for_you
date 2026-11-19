import base64
from urllib.parse import urlparse
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from ..constants import (
    AZURE_BLOB_ACCOUNT_URL2,
    AZURE_STORAGE_ACCOUNT_NAME2,
    AZURE_STORAGE_CONTAINER_NAME2,
)


class AzureBlobService2:
    """Azure Blob Storage 服务类（第二个存储账户）"""

    def __init__(self):
        account_name = AZURE_STORAGE_ACCOUNT_NAME2
        account_url = AZURE_BLOB_ACCOUNT_URL2
        if not account_name or not account_url:
            raise ValueError(
                "Azure Blob Storage 2 认证信息未配置。请在 constants.py 文件中设置 AZURE_STORAGE_ACCOUNT_NAME2 与 AZURE_BLOB_ACCOUNT_URL2")
        self.account_host = urlparse(account_url).hostname
        credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url, credential=credential)

        # 获取容器名称
        self.container_name = AZURE_STORAGE_CONTAINER_NAME2
        if not self.container_name:
            raise ValueError(
                "未配置容器名称。请在 constants.py 文件中设置 AZURE_STORAGE_CONTAINER_NAME2")

    def downloadImageAsBase64(self, image_url: str) -> str:
        """
        根据图片 URL 从 Azure Blob Container 下载图片并返回 base64 编码（带 data 前缀）

        参数:
            image_url: 图片的 URL（完整 URL 或相对路径）

        返回:
            str: 图片的 base64 编码字符串，格式为 "data:image/[type];base64,..."
        """
        try:
            # 从 URL 中提取 blob 名称
            # 支持完整 URL 或相对路径
            blob_name = self._extract_blob_name(image_url)
            # 只允许读取图片，避免被用来读取容器里的其他文件
            mime_type = self._get_mime_type(blob_name)

            # 获取容器客户端
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name)

            import time
            start_time = time.time()
            download_stream = blob_client.download_blob(max_concurrency=4)
            api_time = time.time() - start_time

            chunk_start = time.time()
            # 使用chunks()迭代器增量读取，避免内存积压
            chunks = []
            try:
                for chunk in download_stream.chunks():
                    chunks.append(chunk)
                image_bytes = b''.join(chunks)
            finally:
                # 显式释放下载流资源
                del download_stream
                del chunks
            chunk_time = time.time() - chunk_start
            total_time = time.time() - start_time

            print(
                f"⏱️ Blob下载耗时: API调用 {api_time:.3f}s, 数据读取 {chunk_time:.3f}s, 总计 {total_time:.3f}s - {blob_name}"
            )

            # 转换为 base64
            base64_str = base64.b64encode(image_bytes).decode('utf-8')

            # 添加 data URL 前缀
            data_url = f"data:{mime_type};base64,{base64_str}"

            return data_url

        except Exception as e:
            raise Exception("下载图片失败") from e

    def _extract_blob_name(self, image_url: str) -> str:
        """
        从 URL 中提取 blob 名称

        参数:
            image_url: 图片的 URL

        返回:
            str: blob 名称（相对路径）
        """
        parsed = urlparse(image_url)
        blob_name = ''

        if parsed.scheme in ('http', 'https'):
            # 只接受配置的存储账户，不能指向别的主机
            if parsed.hostname != self.account_host:
                raise ValueError("不支持的图片地址")
            # parsed.path 已去除查询参数
            path_segments = [segment for segment in parsed.path.split('/') if segment]
            if not path_segments:
                raise ValueError(f"无法从 URL 中提取 blob 名称: {image_url}")
            try:
                container_index = path_segments.index(self.container_name)
                blob_segments = path_segments[container_index + 1:]
            except ValueError:
                # 容器名不在路径里，回退为跳过首段
                blob_segments = path_segments[1:]
            blob_name = '/'.join(blob_segments)
        else:
            blob_name = image_url.lstrip('/')

        if not blob_name or '..' in blob_name.split('/'):
            raise ValueError("无法从 URL 中提取 blob 名称")

        # 移除相对路径中的查询/片段（例如 ?sastoken）
        blob_name = blob_name.split('?', 1)[0].split('#', 1)[0]
        return blob_name

    def _get_mime_type(self, blob_name: str) -> str:
        """
        根据文件扩展名获取 MIME 类型

        参数:
            blob_name: blob 名称

        返回:
            str: MIME 类型
        """
        extension = blob_name.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
        }
        if extension not in mime_types:
            raise ValueError("只支持图片文件")
        return mime_types[extension]

import pymysql
from typing import List, Dict, Any
from ..constants import (
	MYSQL_HOST,
	MYSQL_PORT,
	MYSQL_USER,
	MYSQL_PASSWORD,
	MYSQL_DATABASE,
)


class SqlService:
	"""MySQL 数据库服务类"""

	def __init__(self):
		"""初始化数据库连接配置"""
		self.config = {
			'host': MYSQL_HOST,
			'port': MYSQL_PORT,
			'user': MYSQL_USER,
			'password': MYSQL_PASSWORD,
			'database': MYSQL_DATABASE,
			'charset': 'utf8mb4',
			'cursorclass': pymysql.cursors.DictCursor,
		}

	def _get_connection(self):
		"""获取数据库连接"""
		return pymysql.connect(**self.config)

	def get_tasks_by_user_id(self, user_id: str) -> Dict[str, Any]:
		"""
		根据 userId 查询 Tasks 表中的所有匹配行

		参数:
			user_id: 用户 ID

		返回:
			{
				'success': True/False,
				'count': 匹配行数,
				'data': [
					{
						'id': 1,
						'userId': 'xxx',
						'requestId': 'xxx',
						'dateTime': '2025-01-01 12:00:00',
						'bookName': 'xxx',
						'pageRange': '1-10',
						'status': 'completed'
					},
					...
				],
				'error_msg': ''
			}
		"""
		connection = None
		try:
			connection = self._get_connection()
			with connection.cursor() as cursor:
				sql = "SELECT * FROM Tasks WHERE userId = %s ORDER BY dateTime DESC"
				cursor.execute(sql, (user_id,))
				rows = cursor.fetchall()

				# 将 datetime 对象转换为字符串
				for row in rows:
					if row.get('dateTime'):
						row['dateTime'] = row['dateTime'].strftime(
							'%Y-%m-%d %H:%M:%S')

				return {
					'success': True,
					'count': len(rows),
					'data': rows,
					'error_msg': ''
				}

		except Exception as e:
			print(f"❌ SqlService.get_tasks_by_user_id Error: {e}")
			return {
				'success': False,
				'count': 0,
				'data': [],
				'error_msg': str(e)
			}

		finally:
			if connection:
				connection.close()

	def task_belongs_to_user(self, user_id: str, request_id: str) -> bool:
		"""判断 request_id 对应的任务是否属于该用户"""
		connection = None
		try:
			connection = self._get_connection()
			with connection.cursor() as cursor:
				sql = "SELECT 1 FROM Tasks WHERE userId = %s AND requestId = %s LIMIT 1"
				cursor.execute(sql, (user_id, request_id))
				return cursor.fetchone() is not None

		except Exception as e:
			print(f"❌ SqlService.task_belongs_to_user Error: {e}")
			return False

		finally:
			if connection:
				connection.close()

	def insert_task(self, user_id: str, request_id: str, book_name: str, page_range: str, status: str = 'pending') -> Dict[str, Any]:
		"""
		插入一条新的任务记录

		参数:
			user_id: 用户 ID (来自 cookie)
			request_id: 异步识别请求 ID
			book_name: 书籍名称
			page_range: 页码范围
			status: 任务状态，默认 'pending'

		返回:
			{'success': True/False, 'id': 插入的记录ID, 'error_msg': ''}
		"""
		connection = None
		try:
			connection = self._get_connection()
			with connection.cursor() as cursor:
				sql = """
					INSERT INTO Tasks (userId, requestId, dateTime, bookName, pageRange, status)
					VALUES (%s, %s, NOW(), %s, %s, %s)
				"""
				cursor.execute(sql, (user_id, request_id, book_name, page_range, status))
				connection.commit()
				return {
					'success': True,
					'id': cursor.lastrowid,
					'error_msg': ''
				}

		except Exception as e:
			print(f"❌ SqlService.insert_task Error: {e}")
			return {
				'success': False,
				'id': None,
				'error_msg': str(e)
			}

		finally:
			if connection:
				connection.close()

	def update_task_status(self, request_id: str, status: str) -> Dict[str, Any]:
		"""
		更新任务状态

		参数:
			request_id: 异步识别请求 ID
			status: 新状态

		返回:
			{'success': True/False, 'error_msg': ''}
		"""
		connection = None
		try:
			connection = self._get_connection()
			with connection.cursor() as cursor:
				sql = "UPDATE Tasks SET status = %s WHERE requestId = %s"
				cursor.execute(sql, (status, request_id))
				connection.commit()
				return {
					'success': True,
					'error_msg': ''
				}

		except Exception as e:
			print(f"❌ SqlService.update_task_status Error: {e}")
			return {
				'success': False,
				'error_msg': str(e)
			}

		finally:
			if connection:
				connection.close()
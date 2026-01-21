import os
import sqlite3
from contextlib import contextmanager
from typing import Any, List, Dict, Optional, Tuple


class Database:
    """SQLite数据库封装类，提供简单便捷的增删改查操作"""
    
    def __init__(self):
        # 初始化数据库
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, "backup.db")
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor
    
    def fetch_one(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()
    
    def fetch_all(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """查询多条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入数据并返回插入的ID"""
        if not data:
            raise ValueError("插入数据不能为空")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
        """批量插入数据"""
        if not data_list:
            return True
        
        first_item = data_list[0]
        columns = ', '.join(first_item.keys())
        placeholders = ', '.join(['?' for _ in first_item])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        values = [tuple(item.values()) for item in data_list]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, values)
            conn.commit()
            return True
    
    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Tuple = ()) -> int:
        """更新数据并返回影响的行数"""
        if not data:
            raise ValueError("更新数据不能为空")
        
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values()) + where_params
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
    
    def delete(self, table: str, where_clause: str, where_params: Tuple = ()) -> int:
        """删除数据并返回影响的行数"""
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, where_params)
            conn.commit()
            return cursor.rowcount
    
    def select(self, table: str, columns: str = "*", where_clause: str = "", 
               where_params: Tuple = (), order_by: str = "", limit: int = None) -> List[sqlite3.Row]:
        """查询数据"""
        sql = f"SELECT {columns} FROM {table}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        return self.fetch_all(sql, where_params)
    
    def select_one(self, table: str, columns: str = "*", where_clause: str = "", 
                   where_params: Tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条数据"""
        sql = f"SELECT {columns} FROM {table}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        sql += " LIMIT 1"
        
        return self.fetch_one(sql, where_params)
    
    def count(self, table: str, where_clause: str = "", where_params: Tuple = ()) -> int:
        """统计记录数量"""
        sql = f"SELECT COUNT(*) as count FROM {table}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = self.fetch_one(sql, where_params)
        return result['count'] if result else 0
    
    def exists(self, table: str, where_clause: str, where_params: Tuple = ()) -> bool:
        """检查记录是否存在"""
        return self.count(table, where_clause, where_params) > 0
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.fetch_one(sql, (table_name,))
        return result is not None
    
    def create_table(self, table_name: str, columns: Dict[str, str], 
                     primary_key: str = None, auto_increment: bool = False) -> bool:
        """创建表"""
        column_definitions = []
        
        for column, column_type in columns.items():
            if column == primary_key and auto_increment:
                column_definitions.append(f"{column} {column_type} PRIMARY KEY AUTOINCREMENT")
            elif column == primary_key:
                column_definitions.append(f"{column} {column_type} PRIMARY KEY")
            else:
                column_definitions.append(f"{column} {column_type}")
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_definitions)})"
        
        try:
            self.execute(sql)
            return True
        except Exception as e:
            print(f"创建表失败: {e}")
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        try:
            self.execute(f"DROP TABLE IF EXISTS {table_name}")
            return True
        except Exception as e:
            print(f"删除表失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[sqlite3.Row]:
        """获取表结构信息"""
        sql = f"PRAGMA table_info({table_name})"
        return self.fetch_all(sql)




class QueryBuilder:
    """SQL查询构建器"""
    
    def __init__(self, table: str):
        self.table = table
        self._select_columns = "*"
        self._where_conditions = []
        self._where_params = []
        self._order_by = ""
        self._limit = None
        self._offset = None
    
    def select(self, *columns: str):
        """设置查询列"""
        if columns:
            self._select_columns = ', '.join(columns)
        return self
    
    def where(self, condition: str, *params):
        """添加WHERE条件"""
        self._where_conditions.append(condition)
        self._where_params.extend(params)
        return self
    
    def where_in(self, column: str, values: List[Any]):
        """添加IN条件"""
        placeholders = ', '.join(['?' for _ in values])
        self._where_conditions.append(f"{column} IN ({placeholders})")
        self._where_params.extend(values)
        return self
    
    def where_like(self, column: str, pattern: str):
        """添加LIKE条件"""
        self._where_conditions.append(f"{column} LIKE ?")
        self._where_params.append(pattern)
        return self
    
    def order_by(self, column: str, direction: str = "ASC"):
        """设置排序"""
        direction = direction.upper()
        if direction not in ["ASC", "DESC"]:
            direction = "ASC"
        
        if self._order_by:
            self._order_by += f", {column} {direction}"
        else:
            self._order_by = f"{column} {direction}"
        return self
    
    def limit(self, count: int):
        """设置限制数量"""
        self._limit = count
        return self
    
    def offset(self, count: int):
        """设置偏移量"""
        self._offset = count
        return self
    
    def build(self) -> Tuple[str, Tuple]:
        """构建SQL查询语句"""
        sql = f"SELECT {self._select_columns} FROM {self.table}"
        
        if self._where_conditions:
            sql += f" WHERE {' AND '.join(self._where_conditions)}"
        
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        
        if self._limit:
            sql += f" LIMIT {self._limit}"
        
        if self._offset:
            sql += f" OFFSET {self._offset}"
        
        return sql, tuple(self._where_params)

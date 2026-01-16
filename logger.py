import logging
import os
from datetime import datetime

def setup_logger(name='webview_app', level=logging.INFO):
    """设置日志系统"""
    
    # 创建log目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果已经有handler，避免重复添加
    if logger.handlers:
        return logger
    
    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler - 按日期分割
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'webview_app_{today}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认logger
app_logger = setup_logger()

def get_logger(name=None):
    """获取logger实例"""
    if name:
        return setup_logger(name)
    return app_logger
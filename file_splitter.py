import os
from typing import List, Tuple, Optional
from logger import get_logger

logger = get_logger(__name__)

class FileSplitter:
    """文件分割工具类"""

    @staticmethod
    def split_file(input_path: str, output_dir: str, chunk_size_mb: int,
                 mode: str = 'binary', encoding: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        分割文件为指定大小的块

        :param input_path: 输入文件路径
        :param output_dir: 输出目录
        :param chunk_size_mb: 每个分割块的目标大小(MB)
        :param mode: 分割模式 ('binary' 或 'text')
        :param encoding: 文本模式下的编码方式 (如 'utf-8', 'gbk' 等)
        :return: (是否成功, 分割后的文件列表)
        """
        try:
            # 验证输入文件
            if not os.path.isfile(input_path):
                logger.error(f"输入文件不存在: {input_path}")
                return False, []

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 计算分割块大小(字节)
            chunk_size = chunk_size_mb * 1024 * 1024
            file_name = os.path.basename(input_path)
            base_name, ext = os.path.splitext(file_name)

            # 检查是否为CSV文件
            is_csv = ext.lower() == '.csv'
            header_line = None

            if mode == 'binary':
                # 二进制模式分割
                result_files = []
                with open(input_path, 'rb') as f:
                    part_num = 1
                    while True:
                        output_path = os.path.join(output_dir, f"{base_name}.part{part_num}{ext}")
                        data = f.read(chunk_size)
                        if not data:
                            break
                        with open(output_path, 'wb') as out_file:
                            out_file.write(data)
                        result_files.append(output_path)
                        logger.info(f"已生成分割文件: {output_path} (二进制模式)")
                        part_num += 1
                return True, result_files
            else:
                # 文本模式分割
                if not encoding:
                    encoding = 'utf-8'

                result_files = []
                current_size = 0
                part_num = 1
                current_lines = []

                with open(input_path, 'r', encoding=encoding, errors='replace') as f:
                    # 如果是CSV文件，读取并保存表头
                    if is_csv:
                        header_line = f.readline()
                        current_size += len(header_line.encode(encoding))
                        logger.info(f"检测到CSV文件，已读取表头: {header_line.strip()}")

                    for line in f:
                        line_size = len(line.encode(encoding))

                        # 如果当前大小超过目标大小且至少有一行内容，写入新文件
                        if current_size + line_size > chunk_size and current_lines:
                            output_path = os.path.join(output_dir, f"{base_name}.part{part_num}{ext}")
                            with open(output_path, 'w', encoding=encoding) as out_file:
                                # 如果是CSV文件且存在表头，先写入表头
                                if is_csv and header_line:
                                    out_file.write(header_line)
                                out_file.writelines(current_lines)
                            result_files.append(output_path)
                            logger.info(f"已生成分割文件: {output_path} (大小: {current_size/1024/1024:.2f}MB, 编码: {encoding})")

                            # 重置计数器和缓冲区
                            part_num += 1
                            current_size = 0
                            current_lines = []

                            # CSV文件的新分割块需要重新计算表头大小
                            if is_csv and header_line:
                                current_size = len(header_line.encode(encoding))

                        current_lines.append(line)
                        current_size += line_size

                # 写入最后一部分
                if current_lines:
                    output_path = os.path.join(output_dir, f"{base_name}.part{part_num}{ext}")
                    with open(output_path, 'w', encoding=encoding) as out_file:
                        # 如果是CSV文件且存在表头，先写入表头
                        if is_csv and header_line:
                            out_file.write(header_line)
                        out_file.writelines(current_lines)
                    result_files.append(output_path)
                    logger.info(f"已生成分割文件: {output_path} (大小: {current_size/1024/1024:.2f}MB, 编码: {encoding})")

                return True, result_files

        except Exception as e:
            logger.error(f"文件分割失败: {e}")
            return False, []
import os
from openpyxl import load_workbook
from pathlib import Path


class ColumnInfo:
    def __init__(self):
        self.table_name = None
        self.field_name = None
        self.field_type = None
        self.field_meaning = None


# 其他辅助函数（convert_to_camel_case、snake_case_to_camel_case等保持不变）
def convert_to_camel_case(table_name):
    if not table_name:
        return ""
    last_dot_index = table_name.rfind('.')
    if last_dot_index != -1:
        table_name = table_name[last_dot_index + 1:]

    camel_case = []
    capitalize_next = True
    for c in table_name:
        if c == '_':
            capitalize_next = True
        else:
            if capitalize_next:
                camel_case.append(c.upper())
                capitalize_next = False
            else:
                camel_case.append(c)
    return ''.join(camel_case)


def snake_case_to_camel_case(snake_case):
    if not snake_case:
        return ""
    camel_case = []
    capitalize_next = False
    for c in snake_case:
        if c == '_':
            capitalize_next = True
        else:
            if capitalize_next:
                camel_case.append(c.upper())
                capitalize_next = False
            else:
                camel_case.append(c)
    return ''.join(camel_case)


def data_type_converter(db_type):
    type_map = {
        'int': 'Integer',
        'integer': 'Integer',
        'smallint': 'Short',
        'number': 'Integer',
        'bigint': 'Long',
        'decimal': 'BigDecimal',
        'double': 'Double',
        'float': 'Float',
        'long': 'long',
        'varchar': 'String',
        'text': 'String',
        'char': 'String',
        'varchar2': 'String',
        'datetime': 'Date',
        'date': 'Date',
        'timestamp': 'Timestamp',
        'boolean': 'Boolean'
    }
    if not db_type:
        return 'String'
    db_type_lower = db_type.lower()
    ## 对number类型进行特殊处理
    # 判断是否包含逗号
    if 'number' in db_type_lower:
        if ',' in db_type_lower:
            return 'BigDecimal'
        # 判断number括号内是否大于8
        if '(' in db_type_lower and int(db_type_lower.split('(')[1].split(')')[0]) > 8:
            return 'Long'

    for key in type_map:
        if key in db_type_lower:
            return type_map[key]
    return 'String'


def generate_entity_class(class_name, table_name, column_infos):
    # 保持不变
    lines = ["package com.sxzq.crm.model.jxkh.model;", "import lombok.Data;", "",
             "import com.baomidou.mybatisplus.annotation.TableName;", "import java.io.Serializable;", "",
             "import java.math.BigDecimal;", "import java.time.LocalDate;", "", "@Data",
             f"@TableName(\"{table_name}\")", f"public class {class_name} implements Serializable {{",
             "    private static final long serialVersionUID = 1L;", ""]

    for col in column_infos:
        lines.append(f"    /** {col.field_meaning} */")
        java_type = data_type_converter(col.field_type)
        field_name = snake_case_to_camel_case(col.field_name)
        lines.append(f"    private {java_type} {field_name};")
        lines.append("")

    lines.append("}")
    return '\n'.join(lines)


def generate_mapper_class(mapper_class_name, entity_class_name):
    # 保持不变
    lines = ["package com.sxzq.crm.model.dao.lcbiz;", "", "import com.baomidou.mybatisplus.core.mapper.BaseMapper;",
             f"import com.sxzq.crm.model.jxkh.model.{entity_class_name};", "",
             f"public interface {mapper_class_name} extends BaseMapper<{entity_class_name}> {{", "}"]
    return '\n'.join(lines)


def write_code_to_file(code, file_name, output_directory):
    # 保持不变
    os.makedirs(output_directory, exist_ok=True)
    file_path = os.path.join(output_directory, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)

def excel_to_entity_main(excel_file_path, output_directory, start_sheet_index):
    try:
        excel_file_path = Path(excel_file_path)
        output_directory = Path(output_directory)
        if not excel_file_path.exists():
            print(f"错误：文件不存在 - {excel_file_path}")
            return False

        # 保持只读模式（提升性能）
        wb = load_workbook(excel_file_path, read_only=True, data_only=True)
        table_column_map = {}

        sheet_names = wb.sheetnames
        # 从第8个工作表开始读取（索引从0开始）
        start_index = start_sheet_index  # 第8个sheet的索引是7
        for sheet_name in sheet_names[start_index:]:
            sheet = wb[sheet_name]

            max_row = sheet.max_row
            max_col = sheet.max_column

            current_table_name = None
            # 遍历每行数据（从第二行开始，跳过表头）
            for row_idx in range(2, max_row + 1):
                # 处理第一列（表名，A列，索引1）
                # 直接读取单元格值，不处理合并
                table_name_val = sheet.cell(row=row_idx, column=1).value

                # 确保表名不为空且不是数字等无效值
                if (table_name_val is not None and
                    str(table_name_val).strip() and
                    not str(table_name_val).strip().isdigit()):
                    current_table_name = str(table_name_val).strip()

                # 如果当前行没有表名但有有效的字段信息，则使用最近的有效表名
                if not current_table_name:
                    continue

                # 处理字段名（B列，索引2）
                field_name_val = sheet.cell(row=row_idx, column=2).value
                field_name = str(field_name_val).strip() if field_name_val is not None else None
                if not field_name or field_name.isdigit():
                    continue

                # 处理字段类型（C列，索引3）
                field_type_val = sheet.cell(row=row_idx, column=3).value
                field_type = str(field_type_val).strip() if field_type_val is not None else ""

                # 处理字段含义（D列，索引4）
                field_meaning_val = sheet.cell(row=row_idx, column=4).value
                field_meaning = str(field_meaning_val).strip() if field_meaning_val is not None else ""

                column_info = ColumnInfo()
                column_info.table_name = current_table_name
                column_info.field_name = field_name
                column_info.field_type = field_type
                column_info.field_meaning = field_meaning

                if current_table_name not in table_column_map:
                    table_column_map[current_table_name] = []
                table_column_map[current_table_name].append(column_info)
            wb.close()
        # 生成代码（保持不变）
        for table_name, column_infos in table_column_map.items():
            if not table_name or not column_infos:
                continue
            class_name = convert_to_camel_case(table_name)
            #将table_name 前缀替换
            table_name = table_name.replace("crm_res", "lcbiz")
            print(f"生成类: {class_name} (表: {table_name}, 字段数: {len(column_infos)})")

            entity_code = generate_entity_class(class_name, table_name, column_infos)
            write_code_to_file(entity_code, f"{class_name}.java", output_directory)

            mapper_code = generate_mapper_class(f"{class_name}Mapper", class_name)
            write_code_to_file(mapper_code, f"{class_name}Mapper.java", output_directory)

        print(f"实体类和Mapper文件生成成功！共生成 {len(table_column_map)} 个表")
        return True
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
# 移除了合并单元格处理功能，现在直接按行读取单元格值
def main():
    try:
        import os

        # 从环境变量获取参数
        excel_file_path = os.getenv('EXCEL_TO_ENTITY_FILE')
        output_directory = os.getenv('EXCEL_TO_ENTITY_OUTPUT')
        start_sheet_index = int(os.getenv('EXCEL_TO_ENTITY_START_INDEX', '7'))

        if not excel_file_path or not output_directory:
            print("错误：缺少必要的环境变量 EXCEL_TO_ENTITY_FILE 或 EXCEL_TO_ENTITY_OUTPUT")
            return False

        excel_file_path = Path(excel_file_path)
        output_directory = Path(output_directory)

        if not excel_file_path.exists():
            print(f"错误：文件不存在 - {excel_file_path}")
            return False

        # 保持只读模式（提升性能）
        wb = load_workbook(excel_file_path, read_only=True, data_only=True)
        table_column_map = {}

        sheet_names = wb.sheetnames
        # 从第8个工作表开始读取（索引从0开始）
        start_index = 7  # 第8个sheet的索引是7
        for sheet_name in sheet_names[start_index:]:
            sheet = wb[sheet_name]

            max_row = sheet.max_row
            max_col = sheet.max_column

            current_table_name = None
            # 遍历每行数据（从第二行开始，跳过表头）
            for row_idx in range(2, max_row + 1):
                # 处理第一列（表名，A列，索引1）
                # 直接读取单元格值，不处理合并
                table_name_val = sheet.cell(row=row_idx, column=1).value

                # 确保表名不为空且不是数字等无效值
                if (table_name_val is not None and
                    str(table_name_val).strip() and
                    not str(table_name_val).strip().isdigit()):
                    current_table_name = str(table_name_val).strip()

                # 如果当前行没有表名但有有效的字段信息，则使用最近的有效表名
                if not current_table_name:
                    continue

                # 处理字段名（B列，索引2）
                field_name_val = sheet.cell(row=row_idx, column=2).value
                field_name = str(field_name_val).strip() if field_name_val is not None else None
                if not field_name or field_name.isdigit():
                    continue

                # 处理字段类型（C列，索引3）
                field_type_val = sheet.cell(row=row_idx, column=3).value
                field_type = str(field_type_val).strip() if field_type_val is not None else ""

                # 处理字段含义（D列，索引4）
                field_meaning_val = sheet.cell(row=row_idx, column=4).value
                field_meaning = str(field_meaning_val).strip() if field_meaning_val is not None else ""

                column_info = ColumnInfo()
                column_info.table_name = current_table_name
                column_info.field_name = field_name
                column_info.field_type = field_type
                column_info.field_meaning = field_meaning

                if current_table_name not in table_column_map:
                    table_column_map[current_table_name] = []
                table_column_map[current_table_name].append(column_info)

        wb.close()

        # 生成代码（保持不变）
        for table_name, column_infos in table_column_map.items():
            if not table_name or not column_infos:
                continue
            class_name = convert_to_camel_case(table_name)
            #将table_name 前缀替换
            table_name = table_name.replace("crm_res", "lcbiz")
            print(f"生成类: {class_name} (表: {table_name}, 字段数: {len(column_infos)})")

            entity_code = generate_entity_class(class_name, table_name, column_infos)
            write_code_to_file(entity_code, f"{class_name}.java", output_directory)

            mapper_code = generate_mapper_class(f"{class_name}Mapper", class_name)
            write_code_to_file(mapper_code, f"{class_name}Mapper.java", output_directory)

        print(f"实体类和Mapper文件生成成功！共生成 {len(table_column_map)} 个表")
        return True

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
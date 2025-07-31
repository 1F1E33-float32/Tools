import json
import csv
import os

def extract_rows(data):
    """
    自动查找 JSON 中第一个包含 'rows' 列表的字段，
    并返回它的第一个元素下的 rows 列表。
    """
    for key, val in data.items():
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, dict) and 'rows' in first:
                return first['rows']
    raise ValueError("未找到任何包含 'rows' 的列表字段")

def normalize_row(row_strings, num_cols):
    """
    如果某行的 strings 比表头短，则补齐空字符串；如果比表头长则保留全部。
    """
    if len(row_strings) < num_cols:
        return row_strings + [''] * (num_cols - len(row_strings))
    return row_strings

def json_to_csv(json_path, csv_path):
    # 1. 读取 JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 提取 rows
    rows = extract_rows(data)

    # 3. 跳过空行和注释行，第一行作为表头
    valid_rows = [
        r for r in rows
        if not r.get('isEmpty', 0) and not r.get('isCommentOut', 0)
    ]
    if not valid_rows:
        raise ValueError("所有行都被标记为空或注释，无法生成 CSV")

    headers = valid_rows[0]['strings']
    num_cols = len(headers)

    # 4. 写入 CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in valid_rows[1:]:
            row_data = normalize_row(row['strings'], num_cols)
            writer.writerow(row_data)

    print(f"已生成 CSV：{csv_path}")

if __name__ == '__main__':
    # 你可以在这里修改输入／输出路径
    json_file = r"C:\Users\OOPPEENN\Desktop\assets\utageprojectforstory\story0001.book @-8397337379036461376.json"
    csv_file  = r"C:\Users\OOPPEENN\Desktop\assets\utageprojectforstory\story0001.book @-8397337379036461376.csv"
    json_to_csv(json_file, csv_file)
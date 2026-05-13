#!/usr/bin/env python3
"""CSV 导出：读取 Markdown 测试用例表格，输出 UTF-8 BOM + CRLF 的 CSV 文件。

用法: python export_csv.py <test_cases_path> <output_path>
"""

from __future__ import annotations

import csv
import io
import re
import sys


def needs_quoting(s: str) -> bool:
    return '"' in s or ',' in s or '\n' in s


def quote_field(s: str) -> str:
    if needs_quoting(s):
        return '"' + s.replace('"', '""') + '"'
    return s


def parse_test_cases(path: str) -> list[dict]:
    """从 Markdown 文件中解析测试用例表格行。"""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Markdown 表头顺序（11 列）:
    # 用例ID(0) | 模块(1) | 测试层次(2) | 用例标题(3) | 前置条件(4) |
    # 测试步骤(5) | 预期结果(6) | 优先级(7) | 用例类型(8) | 测试标签(9) | 关联测试点(10)
    #  → CSV（9 列）：ID | 模块 | 标题 | 前置 | 步骤 | 预期 | 优先级 | 类型 | 标签

    cases = []
    buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 新用例行以 "| TC-" 或 "| TC_" 开头
        if re.match(r'^\|\s*TC[-_]', stripped):
            if buffer:
                cases.append(_parse_row(buffer))
            buffer = stripped
        elif buffer and stripped.startswith('|') and not re.match(r'^\|---', stripped):
            buffer += '\n' + stripped

    if buffer:
        cases.append(_parse_row(buffer))

    return [c for c in cases if c is not None]


def _parse_row(buf: str) -> dict | None:
    """将 Markdown 单行或多行表记录解析为 CSV 字段。"""
    parts = [p.strip() for p in buf.split('|')]
    # 去掉首尾空元素
    parts = [p for p in parts if p]

    if len(parts) < 10:
        return None

    return {
        'id':     quote_field(parts[0]),
        'module': quote_field(parts[1]),
        'title':  quote_field(parts[3]),
        'precon': quote_field(parts[4]),
        'steps':  quote_field(parts[5].replace('<br>', '\n')),
        'expect': quote_field(parts[6].replace('<br>', '\n')),
        'pri':    quote_field(parts[7]),
        'type':   quote_field(parts[8]),
        'tag':    quote_field(parts[9]) if len(parts) > 9 else '',
    }


def export_csv(test_cases_path: str, output_path: str):
    cases = parse_test_cases(test_cases_path)

    header = '用例ID,模块,用例标题,前置条件,测试步骤,预期结果,优先级,用例类型,测试标签'
    rows = [header]
    for c in cases:
        rows.append(','.join([c['id'], c['module'], c['title'], c['precon'],
                              c['steps'], c['expect'], c['pri'], c['type'], c['tag']]))

    content = '\r\n'.join(rows)
    # UTF-8 BOM
    with open(output_path, 'wb') as f:
        f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))

    print(f"export-csv: {len(cases)} records -> {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python export_csv.py <test_cases_path> <output_path>")
        sys.exit(1)
    export_csv(sys.argv[1], sys.argv[2])

#!/usr/bin/env python3
"""Markdown 测试设计文档导出。

用法: python export_md.py <test_cases_path> <output_path> [module_name] [total_count] [p0] [p1] [p2]
"""

import sys


def export_md(test_cases_path: str, output_path: str,
              module_name: str = "测试模块", total_count: int = 0,
              p0: int = 0, p1: int = 0, p2: int = 0):
    content = f"""# {module_name} 测试设计文档

## 1. 测试目标
验证基于需求的各项功能，覆盖核心路径、分支流程、参数配置、数据边界及组合场景。

## 2. 测试策略
- **用例总数：** {total_count}
- **优先级分布：** P0: {p0} / P1: {p1} / P2: {p2}
- **测试方法：** 四步测试分析法

## 3. 测试用例列表
详见 {test_cases_path}
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"export-md: {total_count} cases -> {output_path}")


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python export_md.py <test_cases_path> <output_path> "
              "[module_name] [total_count] [p0] [p1] [p2]")
        sys.exit(1)

    test_cases_path = args[0]
    output_path = args[1]
    module_name = args[2] if len(args) > 2 else "测试模块"
    total_count = int(args[3]) if len(args) > 3 else 0
    p0 = int(args[4]) if len(args) > 4 else 0
    p1 = int(args[5]) if len(args) > 5 else 0
    p2 = int(args[6]) if len(args) > 6 else 0

    export_md(test_cases_path, output_path, module_name, total_count, p0, p1, p2)

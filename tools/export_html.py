#!/usr/bin/env python3
"""HTML 测试报告导出：生成零依赖、可交互的 HTML 测试设计文档。

用法: python export_html.py <test_cases_path> <output_path> [module_name]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime


# ── Markdown 解析（复用 export_csv.py 逻辑）─────────────────────────

def parse_test_cases(path: str) -> list[dict]:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cases = []
    buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
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
    parts = [p.strip() for p in buf.split('|')]
    parts = [p for p in parts if p]
    if len(parts) < 10:
        return None

    return {
        'id':      parts[0],
        'module':  parts[1],
        'title':   parts[3],
        'precon':  parts[4],
        'steps':   parts[5].replace('<br>', '\n'),
        'expect':  parts[6].replace('<br>', '\n'),
        'priority': parts[7],
        'type':    parts[8],
        'tags':    parts[9] if len(parts) > 9 else '',
    }


# ── 统计计算 ────────────────────────────────────────────────

def compute_stats(cases: list[dict]) -> dict:
    total = len(cases)
    p0 = sum(1 for c in cases if 'P0' in c['priority'])
    p1 = sum(1 for c in cases if 'P1' in c['priority'])
    p2 = sum(1 for c in cases if 'P2' in c['priority'])

    flow = sum(1 for c in cases if '流程' in c['type'])
    param = sum(1 for c in cases if '参数' in c['type'])
    data_c = sum(1 for c in cases if '数据' in c['type'])
    combo = sum(1 for c in cases if '组合' in c['type'])
    neg = sum(1 for c in cases if '负向' in c['type'])
    safe = sum(1 for c in cases if '安全' in c['type'])

    tagged = sum(1 for c in cases if c['tags'].strip())

    return {
        'total': total,
        'p0': p0, 'p1': p1, 'p2': p2,
        'flow': flow, 'param': param, 'data': data_c, 'combo': combo,
        'neg': neg, 'safe': safe,
        'tagged': tagged,
    }


# ── HTML 生成 ─────────────────────────────────────────────────

def generate_html(cases: list[dict], module_name: str) -> str:
    stats = compute_stats(cases)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cases_json = json.dumps(cases, ensure_ascii=False)

    p0_pct = round(stats['p0'] / stats['total'] * 100) if stats['total'] else 0
    p1_pct = round(stats['p1'] / stats['total'] * 100) if stats['total'] else 0
    p2_pct = round(stats['p2'] / stats['total'] * 100) if stats['total'] else 0

    tag_pct = round(stats['tagged'] / stats['total'] * 100) if stats['total'] else 0

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{module_name} — 测试设计报告</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; color: #1a1a2e; line-height: 1.6; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}

/* Header */
.header {{ background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #fff; padding: 32px 40px; border-radius: 12px; margin-bottom: 24px; }}
.header h1 {{ font-size: 24px; font-weight: 600; }}
.header .meta {{ font-size: 13px; opacity: 0.8; margin-top: 6px; }}

/* Stat Cards */
.stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.stat-card {{ background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); text-align: center; }}
.stat-card .value {{ font-size: 32px; font-weight: 700; }}
.stat-card .label {{ font-size: 12px; color: #6b7280; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
.stat-card.p0 {{ border-left: 4px solid #ef4444; }}
.stat-card.p0 .value {{ color: #ef4444; }}
.stat-card.p1 {{ border-left: 4px solid #f59e0b; }}
.stat-card.p1 .value {{ color: #f59e0b; }}
.stat-card.p2 {{ border-left: 4px solid #3b82f6; }}
.stat-card.p2 .value {{ color: #3b82f6; }}
.stat-card.total {{ border-left: 4px solid #8b5cf6; }}
.stat-card.total .value {{ color: #8b5cf6; }}

/* Progress & Pie Section */
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
@media (max-width: 768px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
.chart-box {{ background: #fff; border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
.chart-box h3 {{ font-size: 14px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }}

/* Progress Bars */
.progress-bar {{ margin-bottom: 14px; }}
.progress-bar .bar-label {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }}
.progress-bar .bar-track {{ height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }}
.progress-bar .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.6s ease; }}
.bar-fill.green {{ background: #10b981; }}
.bar-fill.blue {{ background: #3b82f6; }}

/* Inline SVG Pie */
.pie-wrap {{ display: flex; align-items: center; gap: 24px; justify-content: center; }}
.pie-legend {{ font-size: 13px; }}
.pie-legend div {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }}
.pie-legend .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

/* Toolbar */
.toolbar {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
.toolbar input, .toolbar select {{ padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none; transition: border-color 0.2s; }}
.toolbar input:focus, .toolbar select:focus {{ border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }}
.toolbar input {{ flex: 1; min-width: 200px; }}
.btn {{ padding: 8px 18px; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 500; transition: all 0.15s; }}
.btn-primary {{ background: #2563eb; color: #fff; }}
.btn-primary:hover {{ background: #1d4ed8; }}
.btn-outline {{ background: #fff; color: #2563eb; border: 1px solid #2563eb; }}
.btn-outline:hover {{ background: #eff6ff; }}

/* Table */
.table-wrap {{ background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); overflow: hidden; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead {{ background: #f8fafc; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; cursor: pointer; user-select: none; white-space: nowrap; }}
th:hover {{ color: #2563eb; }}
th .sort-icon {{ font-size: 10px; margin-left: 4px; }}
td {{ padding: 10px 14px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }}
tr:hover {{ background: #f8fafc; }}

.pri-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.pri-badge.P0 {{ background: #fef2f2; color: #dc2626; }}
.pri-badge.P1 {{ background: #fffbeb; color: #d97706; }}
.pri-badge.P2 {{ background: #eff6ff; color: #2563eb; }}

.tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; background: #f3f4f6; color: #6b7280; margin-right: 4px; }}

.steps-cell {{ max-width: 280px; }}
.steps-preview {{ cursor: pointer; color: #2563eb; font-size: 12px; }}
.steps-full {{ display: none; white-space: pre-wrap; }}
.steps-full.open {{ display: block; }}

/* Coverage Bar */
.coverage-section {{ margin-bottom: 24px; }}

/* Footer */
.footer {{ text-align: center; font-size: 12px; color: #9ca3af; margin-top: 32px; padding: 16px; }}

/* No results */
.no-results {{ display: none; text-align: center; padding: 40px; color: #9ca3af; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>📋 {module_name} — 测试设计报告</h1>
  <div class="meta">生成时间: {now} · 共 {stats['total']} 条用例</div>
</div>

<!-- Stats Cards -->
<div class="stats-row">
  <div class="stat-card total"><div class="value">{stats['total']}</div><div class="label">总用例数</div></div>
  <div class="stat-card p0"><div class="value">{stats['p0']}</div><div class="label">P0 · 最高</div></div>
  <div class="stat-card p1"><div class="value">{stats['p1']}</div><div class="label">P1 · 高</div></div>
  <div class="stat-card p2"><div class="value">{stats['p2']}</div><div class="label">P2 · 中</div></div>
</div>

<!-- Charts -->
<div class="charts-row">
  <div class="chart-box">
    <h3>📊 覆盖率指标</h3>
    <div class="progress-bar">
      <div class="bar-label"><span>优先级分布 (P0)</span><span>{p0_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill green" style="width:{p0_pct}%"></div></div>
    </div>
    <div class="progress-bar">
      <div class="bar-label"><span>优先级分布 (P1)</span><span>{p1_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill blue" style="width:{p1_pct}%"></div></div>
    </div>
    <div class="progress-bar">
      <div class="bar-label"><span>测试标签覆盖率</span><span>{tag_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill green" style="width:{tag_pct}%"></div></div>
    </div>
  </div>
  <div class="chart-box">
    <h3>🍩 用例类型分布</h3>
    <div class="pie-wrap">
      <svg width="140" height="140" viewBox="0 0 36 36">
        {_pie_svg(stats)}
      </svg>
      <div class="pie-legend">
        <div><span class="dot" style="background:#3b82f6"></span> 功能 {stats['flow']+stats['param']+stats['data']+stats['combo']}</div>
        <div><span class="dot" style="background:#f59e0b"></span> 负向 {stats['neg']}</div>
        <div><span class="dot" style="background:#ef4444"></span> 安全 {stats['safe']}</div>
        {'' if stats['total'] - stats['flow'] - stats['param'] - stats['data'] - stats['combo'] - stats['neg'] - stats['safe'] <= 0 else f'<div><span class="dot" style="background:#8b5cf6"></span> 其他 {stats["total"] - stats["flow"] - stats["param"] - stats["data"] - stats["combo"] - stats["neg"] - stats["safe"]}</div>'}
      </div>
    </div>
  </div>
</div>

<!-- Toolbar -->
<div class="toolbar">
  <input type="text" id="searchInput" placeholder="🔍 搜索用例标题、模块、步骤..." oninput="filterTable()">
  <select id="filterPriority" onchange="filterTable()">
    <option value="">全部优先级</option>
    <option value="P0">P0</option>
    <option value="P1">P1</option>
    <option value="P2">P2</option>
  </select>
  <select id="filterType" onchange="filterTable()">
    <option value="">全部类型</option>
    <option value="功能">功能</option>
    <option value="负向">负向</option>
    <option value="安全">安全</option>
  </select>
  <select id="filterTag" onchange="filterTable()">
    <option value="">全部标签</option>
  </select>
  <button class="btn btn-outline" onclick="resetFilters()">重置</button>
  <button class="btn btn-primary" onclick="downloadCSV()">⬇ 下载 CSV</button>
</div>

<!-- Table -->
<div class="table-wrap">
<table id="testTable">
<thead>
<tr>
  <th onclick="sortTable(0)">用例ID <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(1)">模块 <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(2)">用例标题 <span class="sort-icon">⇅</span></th>
  <th>前置条件</th>
  <th>测试步骤</th>
  <th>预期结果</th>
  <th onclick="sortTable(6)">优先级 <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(7)">类型 <span class="sort-icon">⇅</span></th>
  <th>标签</th>
</tr>
</thead>
<tbody id="tableBody"></tbody>
</table>
</div>
<div class="no-results" id="noResults">未找到匹配的用例</div>

<!-- Footer -->
<div class="footer">
  由 Test Case Generator 生成 · {now}
</div>

</div>

<script>
const cases = {cases_json};

const TAG_SET = new Set();
cases.forEach(c => {{
  (c.tags || '').split(/[,;，；]/).forEach(t => {{
    const trimmed = t.trim();
    if (trimmed) TAG_SET.add(trimmed);
  }});
}});
const tagSelect = document.getElementById('filterTag');
[...TAG_SET].sort().forEach(t => {{
  const opt = document.createElement('option');
  opt.value = t;
  opt.textContent = t;
  tagSelect.appendChild(opt);
}});

let sortCol = -1;
let sortAsc = true;

function renderTable(data) {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = data.map(c => {{
    const tagsHtml = (c.tags || '').split(/[,;，；]/).filter(t => t.trim())
      .map(t => `<span class="tag">${{t.trim()}}</span>`).join('');
    const stepsHtml = c.steps
      ? `<div class="steps-cell"><div class="steps-preview" onclick="this.nextElementSibling.classList.toggle('open');this.style.display='none'">${{c.steps.split('\\n').slice(0,2).join('<br>')}}<br><small>…点击展开</small></div><div class="steps-full">${{c.steps.replace(/\\n/g,'<br>')}}</div></div>`
      : '';
    return `<tr>
      <td><code>${{c.id}}</code></td>
      <td>${{c.module}}</td>
      <td><strong>${{c.title}}</strong></td>
      <td>${{c.precon || '—'}}</td>
      <td>${{stepsHtml || '—'}}</td>
      <td>${{c.expect ? c.expect.replace(/\\n/g,'<br>') : '—'}}</td>
      <td><span class="pri-badge ${{c.priority}}">${{c.priority}}</span></td>
      <td>${{c.type}}</td>
      <td>${{tagsHtml || '—'}}</td>
    </tr>`;
  }}).join('');
}}

function filterTable() {{
  const query = document.getElementById('searchInput').value.toLowerCase();
  const pri = document.getElementById('filterPriority').value;
  const type = document.getElementById('filterType').value;
  const tag = document.getElementById('filterTag').value;

  let filtered = cases;
  if (query) {{
    filtered = filtered.filter(c =>
      (c.title||'').toLowerCase().includes(query) ||
      (c.module||'').toLowerCase().includes(query) ||
      (c.steps||'').toLowerCase().includes(query) ||
      (c.expect||'').toLowerCase().includes(query)
    );
  }}
  if (pri) filtered = filtered.filter(c => c.priority === pri);
  if (type) filtered = filtered.filter(c => c.type === type);
  if (tag) filtered = filtered.filter(c => (c.tags||'').includes(tag));

  renderTable(filtered);
  document.getElementById('noResults').style.display = filtered.length ? 'none' : 'block';
  document.getElementById('testTable').style.display = filtered.length ? '' : 'none';
}}

function resetFilters() {{
  document.getElementById('searchInput').value = '';
  document.getElementById('filterPriority').value = '';
  document.getElementById('filterType').value = '';
  document.getElementById('filterTag').value = '';
  filterTable();
}}

function sortTable(col) {{
  if (sortCol === col) {{ sortAsc = !sortAsc; }}
  else {{ sortCol = col; sortAsc = true; }}
  const keys = ['id','module','title','precon','steps','expect','priority','type','tags'];
  const key = keys[col];
  cases.sort((a,b) => {{
    const va = (a[key]||'').toLowerCase();
    const vb = (b[key]||'').toLowerCase();
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});
  filterTable();
}}

function downloadCSV() {{
  const header = '\\uFEFF用例ID,模块,用例标题,前置条件,测试步骤,预期结果,优先级,用例类型,测试标签';
  const rows = cases.map(c => {{
    const esc = s => {{
      s = (s||'').replace(/\\n/g,'\\n').replace(/"/g,'""');
      return /[",\\n]/.test(s) ? '"'+s+'"' : s;
    }};
    return [esc(c.id),esc(c.module),esc(c.title),esc(c.precon),esc(c.steps),esc(c.expect),c.priority,c.type,c.tags||''].join(',');
  }});
  const csv = header + '\\r\\n' + rows.join('\\r\\n');
  const blob = new Blob([csv], {{type:'text/csv;charset=utf-8'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '{module_name}_测试用例.csv';
  a.click();
  URL.revokeObjectURL(url);
}}

// Init
renderTable(cases);
</script>
</body>
</html>'''


def _pie_svg(stats: dict) -> str:
    """生成内联 SVG 饼图。"""
    total = stats['total']
    if total == 0:
        return '<circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3"/>'

    func_cnt = stats['flow'] + stats['param'] + stats['data'] + stats['combo']
    neg = stats['neg']
    safe = stats['safe']
    other = total - func_cnt - neg - safe

    segments = []
    if func_cnt: segments.append((func_cnt, '#3b82f6'))
    if neg: segments.append((neg, '#f59e0b'))
    if safe: segments.append((safe, '#ef4444'))
    if other: segments.append((other, '#8b5cf6'))

    parts = []
    offset = 0
    for cnt, color in segments:
        dash = round(cnt / total * 100, 1)
        gap = 100 - dash
        parts.append(
            f'<circle cx="18" cy="18" r="15.9" fill="none" '
            f'stroke="{color}" stroke-width="3" '
            f'stroke-dasharray="{dash} {gap}" '
            f'stroke-dashoffset="-{offset}" '
            f'transform="rotate(-90 18 18)"/>'
        )
        offset += dash

    return '\n'.join(parts)


# ── CLI ────────────────────────────────────────────────────────

def export_html(test_cases_path: str, output_path: str, module_name: str = "测试模块"):
    cases = parse_test_cases(test_cases_path)
    html = generate_html(cases, module_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"export-html: {len(cases)} cases -> {output_path}")


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python export_html.py <test_cases_path> <output_path> [module_name]")
        sys.exit(1)

    export_html(args[0], args[1], args[2] if len(args) > 2 else "测试模块")

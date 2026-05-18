#!/usr/bin/env python3
"""多标签 HTML 测试设计报告：仪表盘 + 测试策略 + 测试点 + 模型 + 用例表格 + 门禁。

用法:
  python export_html.py --cases <_test-cases.md> --analysis <_analysis.md> --gate <_verification-phase2.md> --output <output.html> --module <模块名>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 通用 Markdown 解析工具
# ═══════════════════════════════════════════════════════════════

def parse_table(lines: list[str], header_keyword: str = None) -> list[dict]:
    """解析 GFM 表格为 dict 列表。从表头行提取列名。
    若指定 header_keyword，只匹配包含该关键字的表头行。"""
    header_iter = (l for l in lines if '|' in l and not re.match(r'^\s*\|[\s\-:]+\|', l))
    if header_keyword:
        header_iter = (l for l in header_iter if header_keyword in l)
    header_match = re.search(r'\|.*\|', next(header_iter, ''))
    if not header_match:
        return []
    header_line = header_match.group(0)
    headers = [h.strip() for h in header_line.split('|')]
    headers = [h for h in headers if h]

    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped or re.match(r'^\|[\s\-:]+\|', stripped):
            continue
        if stripped.startswith('|'):
            parts = [p.strip() for p in stripped.split('|')]
            parts = parts[1:] if parts and not parts[0] else parts
            # Skip header row (first cell matches first header name)
            if headers and parts and parts[0] == headers[0]:
                continue
            if len(parts) >= len(headers):
                row = {}
                for i, h in enumerate(headers[:len(parts)]):
                    row[h] = parts[i]
                rows.append(row)
    return rows


def parse_sections(text: str, level: int = 2) -> dict[str, str]:
    """按 ## 或 ### 标题拆分文本为 {标题名: 内容}。"""
    sections = {}
    current_key = '_preamble'
    current_lines = []
    marker = '#' * level + ' '

    for line in text.split('\n'):
        if line.startswith(marker) and not line.startswith('#' * (level + 1)):
            if current_lines:
                sections[current_key] = '\n'.join(current_lines).strip()
            current_key = line[len(marker):].strip()
            current_key = re.sub(r'\s*\{[^}]*\}\s*', '', current_key).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_key] = '\n'.join(current_lines).strip()

    return sections


def extract_code_block(text: str, language: str = 'mermaid') -> list[str]:
    """提取指定语言的代码块内容。"""
    blocks = []
    pattern = rf'```{language}\s*\n(.*?)```'
    for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
        blocks.append(match.group(1).strip())
    return blocks


# ═══════════════════════════════════════════════════════════════
# 文件解析器
# ═══════════════════════════════════════════════════════════════

def parse_test_cases(path: str) -> list[dict]:
    """解析 _test-cases.md → 用例列表。"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    cases_raw = parse_table(lines, header_keyword='用例ID')

    cases = []
    for row in cases_raw:
        vals = list(row.values())
        if len(vals) < 9:
            continue
        cases.append({
            'id':       vals[0],
            'module':   vals[1] if len(vals) > 1 else '',
            'title':    vals[3] if len(vals) > 3 else vals[2] if len(vals) > 2 else '',
            'precon':   vals[4] if len(vals) > 4 else '',
            'steps':    (vals[5] if len(vals) > 5 else '').replace('<br>', '\n'),
            'expect':   (vals[6] if len(vals) > 6 else '').replace('<br>', '\n'),
            'priority': vals[7] if len(vals) > 7 else '',
            'type':     vals[8] if len(vals) > 8 else '',
            'tags':     vals[9] if len(vals) > 9 else '',
        })

    return [c for c in cases if c['id']]


def parse_analysis(path: str) -> dict:
    """解析 _analysis.md → 结构化字典。"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = parse_sections(content, level=2)

    result = {
        'strategy': '',
        'test_points': [],
        'models': [],
        'params': '',
        'risks': '',
        'mermaid_blocks': [],
    }

    for key, text in sections.items():
        key_lower = key.strip()
        if '测试策略' in key_lower or '策略' in key_lower:
            result['strategy'] = _extract_list_text(text)
        elif '测试点' in key_lower:
            result['test_points'] = parse_table(text.split('\n'))
        elif '模型' in key_lower:
            result['models'] = _parse_model_sections(text)
        elif '参数' in key_lower:
            result['params'] = text.strip()
        elif '风险' in key_lower:
            result['risks'] = text.strip()

    result['mermaid_blocks'] = extract_code_block(content, 'mermaid')
    return result


def _extract_list_text(text: str) -> list:
    """提取列表项文本。"""
    lines = text.strip().split('\n')
    items = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            items.append(stripped[2:].strip())
        elif stripped.startswith('**') and ('：' in stripped or ':' in stripped):
            items.append(stripped)
    return items


def _parse_model_sections(text: str) -> list[dict]:
    """解析模型区域 → [{title, type, content, table, mermaid}]。"""
    subs = parse_sections(text, level=3)
    models = []
    for title, content in subs.items():
        entry = {'title': title.strip(), 'type': 'text', 'content': content.strip(), 'table': None, 'mermaid': None}
        mermaid_blocks = extract_code_block(content, 'mermaid')
        if mermaid_blocks:
            entry['mermaid'] = mermaid_blocks[0]
            entry['type'] = 'mermaid'
        table_data = parse_table(content.split('\n'))
        if table_data:
            entry['table'] = table_data
            if entry['type'] == 'text':
                entry['type'] = 'table'
        models.append(entry)
    return models


def parse_verification(path: str) -> dict:
    """解析 _verification-phase2.md → 结构化字典。"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = parse_sections(content, level=2)

    result = {
        'verdict': '',
        'verdict_text': '',
        'classification': [],
        'discarded': [],
        'metrics': [],
        'failed_test_points': [],
        'hazard_check': [],
        'fmea_crosscheck': [],
        'summary': '',
        'l4_checklist': '',
    }

    for key, text in sections.items():
        key_lower = key.strip()
        if '校验结论' in key_lower:
            result['verdict_text'] = text.strip()
            m = re.search(r'\*\*结论[：:]\*\*\s*(.+?)(?:\n|$)', text)
            if m:
                verdict_line = m.group(1).strip()
                if 'FAIL' in verdict_line and 'PASS' not in verdict_line.replace('FAIL', ''):
                    result['verdict'] = 'FAIL'
                elif 'PASS_WITH_WARNINGS' in verdict_line:
                    result['verdict'] = 'PASS_WITH_WARNINGS'
                else:
                    result['verdict'] = 'PASS'
            else:
                if '❌ FAIL' in text:
                    result['verdict'] = 'FAIL'
                elif 'PASS_WITH_WARNINGS' in text:
                    result['verdict'] = 'PASS_WITH_WARNINGS'
                else:
                    result['verdict'] = 'PASS'
        elif '分类筛选' in key_lower or '第一层' in key_lower:
            result['classification'] = parse_table(text.split('\n'))
        elif '废弃用例' in key_lower:
            result['discarded'] = parse_table(text.split('\n'))
        elif '量化指标' in key_lower or '第二层' in key_lower:
            result['metrics'] = parse_table(text.split('\n'))
        elif '不达标' in key_lower and '测试点' in key_lower:
            result['failed_test_points'] = parse_table(text.split('\n'))
        elif '高危场景' in key_lower or '第三层' in key_lower:
            result['hazard_check'] = parse_table(text.split('\n'))
        elif '翻车案例' in key_lower or '交叉校验' in key_lower:
            result['fmea_crosscheck'] = parse_table(text.split('\n'))
        elif '综合裁定' in key_lower:
            result['summary'] = text.strip()
        elif '人工审核' in key_lower or '第四层' in key_lower or 'L4' in key_lower:
            result['l4_checklist'] = text.strip()

    return result


# ═══════════════════════════════════════════════════════════════
# 统计计算
# ═══════════════════════════════════════════════════════════════

def compute_stats(cases: list[dict]) -> dict:
    total = len(cases)
    p0 = sum(1 for c in cases if 'P0' in c.get('priority', ''))
    p1 = sum(1 for c in cases if 'P1' in c.get('priority', ''))
    p2 = sum(1 for c in cases if 'P2' in c.get('priority', ''))
    p3 = total - p0 - p1 - p2

    func = sum(1 for c in cases if '功能' in c.get('type', ''))
    neg = sum(1 for c in cases if '负向' in c.get('type', ''))
    safe = sum(1 for c in cases if '安全' in c.get('type', ''))
    boundary = sum(1 for c in cases if '边界' in c.get('type', ''))
    other = total - func - neg - safe - boundary

    tagged = sum(1 for c in cases if c.get('tags', '').strip())

    return {
        'total': total, 'p0': p0, 'p1': p1, 'p2': p2, 'p3': p3,
        'func': func, 'neg': neg, 'safe': safe, 'boundary': boundary, 'other': other,
        'tagged': tagged,
    }


# ═══════════════════════════════════════════════════════════════
# HTML 辅助函数
# ═══════════════════════════════════════════════════════════════

def _esc(s) -> str:
    if s is None:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _pie_svg(stats: dict) -> str:
    total = stats['total']
    if total == 0:
        return '<circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3"/>'
    segments = []
    if stats['func']: segments.append((stats['func'], '#3b82f6'))
    if stats['boundary']: segments.append((stats['boundary'], '#10b981'))
    if stats['neg']: segments.append((stats['neg'], '#f59e0b'))
    if stats['safe']: segments.append((stats['safe'], '#ef4444'))
    if stats['other']: segments.append((stats['other'], '#8b5cf6'))
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


def _verdict_badge(verdict: str) -> str:
    if verdict == 'PASS':
        return '<span class="badge pass">✅ PASS</span>'
    elif verdict == 'PASS_WITH_WARNINGS':
        return '<span class="badge warn">⚠️ PASS_WITH_WARNINGS</span>'
    elif verdict == 'FAIL':
        return '<span class="badge fail">❌ FAIL</span>'
    return ''


def _render_table(headers: list[str], rows: list[dict], key_map: dict = None) -> str:
    if not rows:
        return '<p class="empty-hint">（无数据）</p>'
    if key_map is None:
        key_map = {h: h for h in headers}
    thead = '<tr>' + ''.join(f'<th>{_esc(h)}</th>' for h in headers) + '</tr>'
    tbody = ''
    for row in rows:
        tds = ''
        for h in headers:
            key = key_map.get(h, h)
            val = row.get(key, '')
            if val is None:
                val = ''
            tds += f'<td>{_esc(str(val))}</td>'
        tbody += f'<tr>{tds}</tr>'
    return f'<div class="mini-table-wrap"><table class="mini-table"><thead>{thead}</thead><tbody>{tbody}</tbody></table></div>'


def _mermaid_block(code: str) -> str:
    escaped = _esc(code)
    return f'''<div class="mermaid-block">
<div class="mermaid-header">🔧 Mermaid 流程图</div>
<pre class="mermaid-code">{escaped}</pre>
<p class="mermaid-hint">💡 复制到 <a href="https://mermaid.live" target="_blank" rel="noopener">mermaid.live</a> 在线渲染</p>
</div>'''


# ═══════════════════════════════════════════════════════════════
# Tab: 仪表盘
# ═══════════════════════════════════════════════════════════════

def tab_dashboard(stats: dict, analysis: dict, verification: dict) -> str:
    p0_pct = round(stats['p0'] / stats['total'] * 100) if stats['total'] else 0
    p1_pct = round(stats['p1'] / stats['total'] * 100) if stats['total'] else 0
    tag_pct = round(stats['tagged'] / stats['total'] * 100) if stats['total'] else 0
    tp_count = len(analysis.get('test_points', []))
    verdict = verification.get('verdict', '')
    verdict_html = _verdict_badge(verdict) if verdict else '—'

    return f'''
<div class="stats-row">
  <div class="stat-card total"><div class="value">{stats['total']}</div><div class="label">总用例数</div></div>
  <div class="stat-card p0"><div class="value">{stats['p0']}</div><div class="label">P0 · 最高</div></div>
  <div class="stat-card p1"><div class="value">{stats['p1']}</div><div class="label">P1 · 高</div></div>
  <div class="stat-card p2"><div class="value">{stats['p2']}</div><div class="label">P2 · 中</div></div>
</div>
<div class="charts-row">
  <div class="chart-box">
    <h3>📊 覆盖率指标</h3>
    <div class="progress-bar">
      <div class="bar-label"><span>优先级分布 (P0)</span><span>{p0_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill red" style="width:{p0_pct}%"></div></div>
    </div>
    <div class="progress-bar">
      <div class="bar-label"><span>优先级分布 (P1)</span><span>{p1_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill blue" style="width:{p1_pct}%"></div></div>
    </div>
    <div class="progress-bar">
      <div class="bar-label"><span>测试标签覆盖</span><span>{tag_pct}%</span></div>
      <div class="bar-track"><div class="bar-fill green" style="width:{tag_pct}%"></div></div>
    </div>
  </div>
  <div class="chart-box">
    <h3>🍩 用例类型分布</h3>
    <div class="pie-wrap">
      <svg width="140" height="140" viewBox="0 0 36 36">{_pie_svg(stats)}</svg>
      <div class="pie-legend">
        <div><span class="dot" style="background:#3b82f6"></span> 功能 {stats['func']}</div>
        {f'<div><span class="dot" style="background:#10b981"></span> 边界 {stats["boundary"]}</div>' if stats['boundary'] else ''}
        <div><span class="dot" style="background:#f59e0b"></span> 负向 {stats['neg']}</div>
        <div><span class="dot" style="background:#ef4444"></span> 安全 {stats['safe']}</div>
        {f'<div><span class="dot" style="background:#8b5cf6"></span> 其他 {stats["other"]}</div>' if stats['other'] else ''}
      </div>
    </div>
  </div>
</div>
<div class="info-cards">
  <div class="info-card"><div class="info-card-title">📋 测试点</div><div class="info-card-value">{tp_count}</div></div>
  <div class="info-card"><div class="info-card-title">🏷️ 标签覆盖</div><div class="info-card-value">{stats['tagged']}/{stats['total']}</div></div>
  <div class="info-card"><div class="info-card-title">🚦 门禁结论</div><div class="info-card-value">{verdict_html}</div></div>
</div>'''


# ═══════════════════════════════════════════════════════════════
# Tab: 测试策略
# ═══════════════════════════════════════════════════════════════

def tab_strategy(analysis: dict) -> str:
    strategy_items = analysis.get('strategy', [])
    if not strategy_items:
        return '<p class="empty-hint">（测试策略未生成）</p>'

    html = '<div class="strategy-list">'
    for item in strategy_items:
        item_esc = _esc(item)
        if '：' in item:
            label, _, rest = item.partition('：')
            html += f'<div class="strategy-item"><strong>{_esc(label)}：</strong>{_esc(rest)}</div>'
        elif ':' in item:
            label, _, rest = item.partition(':')
            html += f'<div class="strategy-item"><strong>{_esc(label)}：</strong>{_esc(rest)}</div>'
        else:
            html += f'<div class="strategy-item">{item_esc}</div>'
    html += '</div>'

    risks = analysis.get('risks', '')
    if risks:
        html += '<h4 style="margin-top:24px">⚠️ 风险与假设</h4>'
        html += f'<div class="strategy-list"><div class="strategy-item">{_esc(risks)}</div></div>'
    return html


# ═══════════════════════════════════════════════════════════════
# Tab: 测试点清单
# ═══════════════════════════════════════════════════════════════

def tab_test_points(analysis: dict) -> str:
    points = analysis.get('test_points', [])
    if not points:
        return '<p class="empty-hint">（测试点清单未生成）</p>'
    headers = ['编号', '测试点', '类型', '风险', '建议测试标签', '说明']
    key_map = {h: h for h in headers}
    return _render_table(headers, points, key_map)


# ═══════════════════════════════════════════════════════════════
# Tab: 模型
# ═══════════════════════════════════════════════════════════════

def tab_models(analysis: dict) -> str:
    models = analysis.get('models', [])
    mermaid_blocks = analysis.get('mermaid_blocks', [])
    html_parts = []

    for code in mermaid_blocks:
        html_parts.append(_mermaid_block(code))

    for model in models:
        title = model.get('title', '')
        html_parts.append(f'<h4 class="model-subtitle">{_esc(title)}</h4>')
        if model.get('mermaid'):
            html_parts.append(_mermaid_block(model['mermaid']))
        elif model.get('table'):
            t = model['table']
            if t:
                headers = list(t[0].keys())
                html_parts.append(_render_table(headers, t))
        elif model.get('content'):
            html_parts.append(f'<pre class="model-text">{_esc(model["content"])}</pre>')

    if not html_parts:
        return '<p class="empty-hint">（模型未生成）</p>'
    return '\n'.join(html_parts)


# ═══════════════════════════════════════════════════════════════
# Tab: 用例表格
# ═══════════════════════════════════════════════════════════════

def tab_cases(cases: list[dict], module_name: str) -> str:
    cases_json = json.dumps(cases, ensure_ascii=False).replace('</', '<\\/')

    tag_set = set()
    for c in cases:
        tags = (c.get('tags') or '').split(',')
        for t in tags:
            t = t.strip()
            if t:
                tag_set.add(t)

    tag_options = '\n'.join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in sorted(tag_set))

    return f'''
<div class="toolbar">
  <input type="text" id="searchInput" placeholder="🔍 搜索用例标题、模块、步骤..." oninput="filterTable()">
  <select id="filterPriority" onchange="filterTable()">
    <option value="">全部优先级</option>
    <option value="P0">P0</option><option value="P1">P1</option><option value="P2">P2</option><option value="P3">P3</option>
  </select>
  <select id="filterType" onchange="filterTable()">
    <option value="">全部类型</option>
    <option value="功能">功能</option><option value="负向">负向</option><option value="边界">边界</option>
    <option value="安全">安全</option><option value="组合">组合</option><option value="错误推测">错误推测</option>
  </select>
  <select id="filterTag" onchange="filterTable()"><option value="">全部标签</option>{tag_options}</select>
  <button class="btn btn-outline" onclick="resetFilters()">重置</button>
  <button class="btn btn-primary" onclick="downloadCSV()">⬇ 下载 CSV</button>
</div>
<div class="table-wrap">
<table id="testTable">
<thead><tr>
  <th onclick="sortTable(0)">用例ID <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(1)">模块 <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(2)">用例标题 <span class="sort-icon">⇅</span></th>
  <th>前置条件</th><th>测试步骤</th><th>预期结果</th>
  <th onclick="sortTable(6)">优先级 <span class="sort-icon">⇅</span></th>
  <th onclick="sortTable(7)">类型 <span class="sort-icon">⇅</span></th>
  <th>标签</th></tr>
</thead>
<tbody id="tableBody"></tbody>
</table>
</div>
<div class="no-results" id="noResults">未找到匹配的用例</div>
<script>
var cases = {cases_json};
var sortCol = -1;
var sortAsc = true;
function esc(s) {{ var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }}
function br(s) {{ return esc(s).replace(/\\n/g, "<br>"); }}
function renderTable(data) {{
  var rows = [];
  data.forEach(function(c) {{
    var tags = (c.tags || "").split(/[,;，；]/).filter(function(t) {{ return t.trim(); }});
    var tagsHtml = tags.length ? tags.map(function(t) {{ return "<span class=\\"tag\\">" + esc(t.trim()) + "</span>"; }}).join("") : "\u2014";
    var stepsHtml = "\u2014";
    if (c.steps) {{
      var preview = esc(c.steps.split("\\n").slice(0,2).join("\\n"));
      var full = br(c.steps);
      stepsHtml = "<div class=\\"steps-cell\\"><div class=\\"steps-preview\\" onclick=\\"var n=this.nextElementSibling;n.classList.toggle(\'open\');this.style.display=n.classList.contains(\'open\')?\'none\':\'\'\\">" + preview + "<br><small>\u2026\u70b9\u51fb\u5c55\u5f00</small></div><div class=\\"steps-full\\">" + full + "</div></div>";
    }}
    rows.push("<tr>" +
      "<td><code>" + esc(c.id) + "</code></td>" +
      "<td>" + esc(c.module) + "</td>" +
      "<td><strong>" + esc(c.title) + "</strong></td>" +
      "<td>" + esc(c.precon || "\u2014") + "</td>" +
      "<td>" + stepsHtml + "</td>" +
      "<td>" + (c.expect ? br(c.expect) : "\u2014") + "</td>" +
      "<td><span class=\\"pri-badge " + esc(c.priority) + "\\">" + esc(c.priority) + "</span></td>" +
      "<td>" + esc(c.type) + "</td>" +
      "<td>" + tagsHtml + "</td></tr>");
  }});
  document.getElementById("tableBody").innerHTML = rows.join("");
}}
function filterTable() {{
  var q = document.getElementById("searchInput").value.toLowerCase();
  var pri = document.getElementById("filterPriority").value;
  var type = document.getElementById("filterType").value;
  var tag = document.getElementById("filterTag").value;
  var filtered = cases;
  if (q) filtered = filtered.filter(function(c) {{ return (c.title||""+c.module||""+c.steps||""+c.expect||"").toLowerCase().indexOf(q) !== -1; }});
  if (pri) filtered = filtered.filter(function(c) {{ return c.priority === pri; }});
  if (type) filtered = filtered.filter(function(c) {{ return c.type === type; }});
  if (tag) filtered = filtered.filter(function(c) {{ return (c.tags||"").indexOf(tag) !== -1; }});
  renderTable(filtered);
  document.getElementById("noResults").style.display = filtered.length ? "none" : "block";
  document.getElementById("testTable").style.display = filtered.length ? "" : "none";
}}
function resetFilters() {{
  document.getElementById("searchInput").value = "";
  document.getElementById("filterPriority").value = "";
  document.getElementById("filterType").value = "";
  document.getElementById("filterTag").value = "";
  filterTable();
}}
function sortTable(col) {{
  if (sortCol === col) sortAsc = !sortAsc; else {{ sortCol = col; sortAsc = true; }}
  var keys = ["id","module","title","precon","steps","expect","priority","type","tags"];
  cases.sort(function(a,b) {{ var va=(a[keys[col]]||"").toLowerCase(), vb=(b[keys[col]]||"").toLowerCase(); return va<vb ? (sortAsc?-1:1) : va>vb ? (sortAsc?1:-1) : 0; }});
  filterTable();
}}
function downloadCSV() {{
  var header = "\\uFEFF用例ID,模块,用例标题,前置条件,测试步骤,预期结果,优先级,用例类型,测试标签";
  var rows = cases.map(function(c) {{
    var ec = function(s) {{ s=(s||"").replace(/"/g,"\\"\\""); return /[",\\n]/.test(s) ? "\\""+s+"\\"" : s; }};
    return [ec(c.id),ec(c.module),ec(c.title),ec(c.precon),ec(c.steps),ec(c.expect),c.priority,c.type,c.tags||""].join(",");
  }});
  var blob = new Blob([header+"\\r\\n"+rows.join("\\r\\n")], {{type:"text/csv;charset=utf-8"}});
  var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "{_esc(module_name)}_测试用例.csv"; a.click();
}}
renderTable(cases);
</script>'''


# ═══════════════════════════════════════════════════════════════
# Tab: 门禁报告
# ═══════════════════════════════════════════════════════════════

def tab_gatekeeper(verification: dict) -> str:
    parts = []

    verdict = verification.get('verdict', '')
    if verdict:
        parts.append(f'<div class="verdict-banner">{_verdict_badge(verdict)}</div>')
    verdict_text = verification.get('verdict_text', '')
    if verdict_text:
        parts.append(f'<pre class="verdict-text">{_esc(verdict_text)}</pre>')

    classification = verification.get('classification', [])
    if classification:
        parts.append('<h4>📊 分类筛选 (L2)</h4>')
        parts.append(_render_table(list(classification[0].keys()), classification))

    discarded = verification.get('discarded', [])
    if discarded:
        parts.append('<h4>❌ 废弃用例</h4>')
        parts.append(_render_table(list(discarded[0].keys()), discarded))

    metrics = verification.get('metrics', [])
    if metrics:
        parts.append('<h4>📏 量化指标 (L3)</h4>')
        parts.append(_render_table(list(metrics[0].keys()), metrics))

    failed = verification.get('failed_test_points', [])
    if failed:
        parts.append('<h4>🔴 未达标测试点</h4>')
        parts.append(_render_table(list(failed[0].keys()), failed))

    hazard = verification.get('hazard_check', [])
    if hazard:
        parts.append('<h4>⚠️ 高危场景核查 (L3)</h4>')
        parts.append(_render_table(list(hazard[0].keys()), hazard))

    fmea = verification.get('fmea_crosscheck', [])
    if fmea:
        parts.append('<h4>🔄 翻车案例交叉校验</h4>')
        parts.append(_render_table(list(fmea[0].keys()), fmea))

    summary = verification.get('summary', '')
    if summary:
        parts.append('<h4>📝 综合裁定</h4>')
        parts.append(f'<div class="strategy-list"><div class="strategy-item">{_esc(summary)}</div></div>')

    l4 = verification.get('l4_checklist', '')
    if l4:
        parts.append('<h4>👁️ L4 人工审核清单</h4>')
        parts.append(f'<pre class="model-text">{_esc(l4)}</pre>')

    if not parts:
        return '<p class="empty-hint">（门禁报告未生成）</p>'
    return '\n'.join(parts)


# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════

CSS = r'''
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; color: #1a1a2e; line-height: 1.6; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }
.header { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #fff; padding: 32px 40px; border-radius: 12px; margin-bottom: 24px; }
.header h1 { font-size: 24px; font-weight: 600; }
.header .meta { font-size: 13px; opacity: 0.8; margin-top: 6px; }

/* Tabs */
.tab-nav { display: flex; gap: 4px; margin-bottom: 0; background: #fff; border-radius: 10px 10px 0 0; padding: 8px 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.tab-btn { padding: 10px 20px; border: none; background: transparent; font-size: 14px; color: #6b7280; cursor: pointer; border-radius: 8px 8px 0 0; transition: all 0.15s; font-weight: 500; }
.tab-btn:hover { color: #2563eb; background: #eff6ff; }
.tab-btn.active { color: #2563eb; background: #fff; box-shadow: 0 -2px 0 #2563eb; }
.tab-content { display: none; background: #fff; border-radius: 0 0 10px 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 24px; }
.tab-content.active { display: block; }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); text-align: center; border: 1px solid #f3f4f6; }
.stat-card .value { font-size: 32px; font-weight: 700; }
.stat-card .label { font-size: 12px; color: #6b7280; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-card.p0 { border-left: 4px solid #ef4444; } .stat-card.p0 .value { color: #ef4444; }
.stat-card.p1 { border-left: 4px solid #f59e0b; } .stat-card.p1 .value { color: #f59e0b; }
.stat-card.p2 { border-left: 4px solid #3b82f6; } .stat-card.p2 .value { color: #3b82f6; }
.stat-card.total { border-left: 4px solid #8b5cf6; } .stat-card.total .value { color: #8b5cf6; }

.info-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 24px; }
.info-card { background: #fff; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid #f3f4f6; text-align: center; }
.info-card-title { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.info-card-value { font-size: 20px; font-weight: 600; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
@media (max-width: 768px) { .charts-row { grid-template-columns: 1fr; } .tab-btn { padding: 8px 12px; font-size: 12px; } }
.chart-box { background: #fff; border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid #f3f4f6; }
.chart-box h3 { font-size: 14px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }

.progress-bar { margin-bottom: 14px; }
.progress-bar .bar-label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.progress-bar .bar-track { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.progress-bar .bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.bar-fill.green { background: #10b981; }
.bar-fill.blue { background: #3b82f6; }
.bar-fill.red { background: #ef4444; }

.pie-wrap { display: flex; align-items: center; gap: 24px; justify-content: center; }
.pie-legend { font-size: 13px; }
.pie-legend div { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.pie-legend .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }

/* Strategy */
.strategy-list { padding: 8px 0; }
.strategy-item { padding: 8px 0; border-bottom: 1px solid #f3f4f6; line-height: 1.8; }
.strategy-item:last-child { border-bottom: none; }

/* Models */
.model-subtitle { font-size: 16px; color: #374151; margin: 20px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #e5e7eb; }
.mermaid-block { background: #1e293b; border-radius: 8px; padding: 16px; margin: 12px 0; }
.mermaid-header { color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.mermaid-code { color: #e2e8f0; font-family: "SF Mono", "Fira Code", monospace; font-size: 13px; white-space: pre-wrap; overflow-x: auto; }
.mermaid-hint { color: #64748b; font-size: 12px; margin-top: 8px; }
.mermaid-hint a { color: #60a5fa; }
.model-text { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; }

/* Tables */
.mini-table-wrap { overflow-x: auto; margin: 12px 0; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mini-table th { background: #f8fafc; padding: 8px 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; white-space: nowrap; }
.mini-table td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
.mini-table tr:hover { background: #f8fafc; }

/* Toolbar */
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.toolbar input, .toolbar select { padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.toolbar input:focus, .toolbar select:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.toolbar input { flex: 1; min-width: 180px; }
.btn { padding: 8px 18px; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 500; transition: all 0.15s; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-outline { background: #fff; color: #2563eb; border: 1px solid #2563eb; }
.btn-outline:hover { background: #eff6ff; }

/* Case Table */
.table-wrap { overflow: hidden; }
#testTable { width: 100%; border-collapse: collapse; font-size: 13px; }
#testTable thead { background: #f8fafc; }
#testTable th { padding: 12px 14px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; cursor: pointer; user-select: none; white-space: nowrap; }
#testTable th:hover { color: #2563eb; }
#testTable th .sort-icon { font-size: 10px; margin-left: 4px; }
#testTable td { padding: 10px 14px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
#testTable tr:hover { background: #f8fafc; }
.pri-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.pri-badge.P0 { background: #fef2f2; color: #dc2626; }
.pri-badge.P1 { background: #fffbeb; color: #d97706; }
.pri-badge.P2 { background: #eff6ff; color: #2563eb; }
.pri-badge.P3 { background: #f3f4f6; color: #6b7280; }
.tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; background: #f3f4f6; color: #6b7280; margin-right: 4px; }
.steps-cell { max-width: 280px; }
.steps-preview { cursor: pointer; color: #2563eb; font-size: 12px; }
.steps-full { display: none; white-space: pre-wrap; }
.steps-full.open { display: block; }
.no-results { display: none; text-align: center; padding: 40px; color: #9ca3af; }

/* Gatekeeper */
.verdict-banner { margin-bottom: 16px; }
.badge { display: inline-block; padding: 6px 16px; border-radius: 6px; font-size: 16px; font-weight: 600; }
.badge.pass { background: #d1fae5; color: #059669; }
.badge.warn { background: #fffbeb; color: #d97706; }
.badge.fail { background: #fef2f2; color: #dc2626; }
.verdict-text { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; margin-bottom: 16px; }
.gatekeeper h4 { font-size: 15px; color: #374151; margin: 20px 0 8px; }
.gatekeeper h4:first-of-type { margin-top: 0; }

.footer { text-align: center; font-size: 12px; color: #9ca3af; margin-top: 32px; padding: 16px; }
.empty-hint { color: #9ca3af; font-style: italic; padding: 20px; text-align: center; }
'''


# ═══════════════════════════════════════════════════════════════
# 主 HTML 组装
# ═══════════════════════════════════════════════════════════════

def generate_html(cases: list[dict], analysis: dict, verification: dict, module_name: str) -> str:
    stats = compute_stats(cases)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    verdict = verification.get('verdict', '') if verification else ''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{module_name} — 完整测试设计报告</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>📋 {module_name} — 完整测试设计报告</h1>
  <div class="meta">生成时间: {now} · 共 {stats['total']} 条用例 · 门禁: {verdict or '—'}</div>
</div>

<div class="tab-nav">
  <button class="tab-btn active" onclick="switchTab('dashboard')">📊 仪表盘</button>
  <button class="tab-btn" onclick="switchTab('strategy')">📋 测试策略</button>
  <button class="tab-btn" onclick="switchTab('testpoints')">🎯 测试点</button>
  <button class="tab-btn" onclick="switchTab('models')">🔧 模型</button>
  <button class="tab-btn" onclick="switchTab('cases')">📝 用例表格</button>
  <button class="tab-btn" onclick="switchTab('gate')">✅ 门禁</button>
</div>

<div class="tab-content active" id="tab-dashboard">
  {tab_dashboard(stats, analysis, verification)}
</div>

<div class="tab-content" id="tab-strategy">
  {tab_strategy(analysis)}
</div>

<div class="tab-content" id="tab-testpoints">
  {tab_test_points(analysis)}
</div>

<div class="tab-content" id="tab-models">
  {tab_models(analysis)}
</div>

<div class="tab-content" id="tab-cases">
  {tab_cases(cases, module_name)}
</div>

<div class="tab-content gatekeeper" id="tab-gate">
  {tab_gatekeeper(verification)}
</div>

<div class="footer">
  由 Test Case Generator v1.0 生成 · {now}
</div>

</div>

<script>
function switchTab(tabId) {{
  document.querySelectorAll('.tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
  document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
  document.getElementById('tab-' + tabId).classList.add('active');
  var tabMap = {{'dashboard':0,'strategy':1,'testpoints':2,'models':3,'cases':4,'gate':5}};
  document.querySelectorAll('.tab-btn')[tabMap[tabId]].classList.add('active');
}}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='生成多标签 HTML 测试设计报告')
    parser.add_argument('--cases', required=True, help='_test-cases.md 路径')
    parser.add_argument('--analysis', default='', help='_analysis.md 路径（可选）')
    parser.add_argument('--gate', default='', help='_verification-phase2.md 路径（可选）')
    parser.add_argument('--output', required=True, help='输出 HTML 文件路径')
    parser.add_argument('--module', default='测试模块', help='模块/功能名称')
    args = parser.parse_args()

    cases = parse_test_cases(args.cases)

    analysis = {}
    if args.analysis:
        try:
            analysis = parse_analysis(args.analysis)
        except Exception as e:
            print(f"Warning: 解析 _analysis.md 失败: {e}", file=sys.stderr)

    verification = {}
    if args.gate:
        try:
            verification = parse_verification(args.gate)
        except Exception as e:
            print(f"Warning: 解析 _verification-phase2.md 失败: {e}", file=sys.stderr)

    html = generate_html(cases, analysis, verification, args.module)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    tabs = []
    if analysis:
        tabs.extend(['策略', f'测试点×{len(analysis.get("test_points", []))}', '模型'])
    tabs.append(f'用例×{len(cases)}')
    if verification:
        tabs.append('门禁')

    print(f"export-html: ✅ {args.output}")
    print(f"  标签: 仪表盘 | {' | '.join(tabs)}")


if __name__ == '__main__':
    main()

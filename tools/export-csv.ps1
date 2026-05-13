param([string]$TestCasesPath, [string]$OutputPath)

$content = [System.IO.File]::ReadAllText($TestCasesPath, [System.Text.Encoding]::UTF8)
$lines = $content -split "`n"

$rows = @()
$rows += "用例ID,模块,用例标题,前置条件,测试步骤,预期结果,优先级,用例类型,测试标签"
$count = 0

function Q([string]$s) {
    if ($s.Contains('"') -or $s.Contains(',') -or $s.Contains("`n")) { return '"' + $s.Replace('"', '""') + '"' }
    return $s
}

# Markdown col: ID(0) | 模块(1) | 测试层次(2) | 标题(3) | 前置(4) | 步骤(5) | 预期(6) | 优先级(7) | 类型(8) | 标签(9) | 关联测试点(10)
# CSV col:      ID(0) | 模块(1) |             标题(3) | 前置(4) | 步骤(5) | 预期(6) | 优先级(7) | 类型(8) | 标签(9)
function ParseRow([string]$buf) {
    $buf = $buf.Trim()
    $parts = $buf -split '\|' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    if ($parts.Count -ge 10) {
        $id    = Q $parts[0]
        $mod   = Q $parts[1]
        $title = Q $parts[3]
        $pre   = Q $parts[4]
        $steps = Q ($parts[5] -replace '<br>', "`n")
        $exp   = Q ($parts[6] -replace '<br>', "`n")
        $pri   = Q $parts[7]
        $type  = Q $parts[8]
        $tag   = Q $parts[9]
        $script:rows += "$id,$mod,$title,$pre,$steps,$exp,$pri,$type,$tag"
        $script:count++
    }
}

$buffer = ""
foreach ($line in $lines) {
    $t = $line.Trim()
    if ($t -eq '') { continue }
    if ($t -match '^\| TC-') {
        if ($buffer -ne '') { ParseRow $buffer }
        $buffer = $t
    }
    elseif ($buffer -ne '' -and $t -match '^\|' -and $t -notmatch '^\|---') {
        $buffer += "`n" + $t
    }
}
if ($buffer -ne '') { ParseRow $buffer }

$csv = $rows -join "`r`n"
$utf8 = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($OutputPath, $csv, $utf8)
Write-Host "export-csv: $count records -> $OutputPath"

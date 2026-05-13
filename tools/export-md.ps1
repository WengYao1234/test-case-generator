<#
.SYNOPSIS
    生成测试设计文档 Markdown 文件
.PARAMETER TestCasesPath
    _test-cases.md 的完整路径
.PARAMETER OutputPath
    输出 Markdown 文件的完整路径
.PARAMETER ModuleName
    模块名称
.PARAMETER TotalCount
    用例总数
.PARAMETER P0/P1/P2
    优先级分布
#>

param(
    [string]$TestCasesPath,
    [string]$OutputPath,
    [string]$ModuleName = "测试模块",
    [int]$TotalCount = 0,
    [int]$P0 = 0,
    [int]$P1 = 0,
    [int]$P2 = 0
)

$md = @"
# $ModuleName 测试设计文档

## 1. 测试目标
验证基于需求的各项功能，覆盖核心路径、分支流程、参数配置、数据边界及组合场景。

## 2. 测试策略
- **用例总数：** $TotalCount
- **优先级分布：** P0: $P0 / P1: $P1 / P2: $P2
- **测试方法：** 四步测试分析法

## 3. 测试用例列表
详见 $TestCasesPath
"@

[System.IO.File]::WriteAllText($OutputPath, $md, [System.Text.Encoding]::UTF8)
Write-Host "export-md: $TotalCount cases -> $OutputPath"

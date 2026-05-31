---
name: openalex-literature-fetcher
description: >
  批量获取学术文献元数据（标题、作者、期刊、年份、卷期、DOI、摘要）并导出为结构化表格。
  通过 OpenAlex 免费 API 搜索，支持任意期刊、任意关键词、任意年份范围，自动翻页和去重。
  适用于文献综述前期的系统检索、国社科/自科申请书参考文献整理、开题报告等场景。
agent_created: true
---

# OpenAlex Literature Fetcher

通过 OpenAlex 免费 API 批量获取学术文献的题录信息（含摘要），支持任意期刊和关键词组合，输出 XLSX + Markdown。

## 核心能力

1. **文献检索** — 按期刊名 + 关键词 + 年份范围批量搜索文献
2. **元数据提取** — 自动获取年份、作者、标题、期刊、卷号、期号、DOI、摘要
3. **去重** — 基于 DOI 自动去重（多个关键词可能命中同一篇文章）
4. **多格式导出** — 同时输出 XLSX 和 Markdown 两种格式
5. **期刊自动识别** — 输入期刊名称即可自动匹配 OpenAlex Source ID

## 使用方式

### 方式 A: CLI 命令行（适合所有 AI agent 直接调用）

```bash
python scripts/cli.py \\
  --journals "Journal of International Economics, Journal of International Money and Finance" \\
  --keywords "tail risk, exchange rate, financial contagion" \\
  --year-start 2020 --year-end 2025 \\
  --output ./results/my_literature
```

参数说明：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--journals` | ✅ | 期刊名，逗号分隔。如 `"AER, JIE, JIMF"` |
| `--keywords` | ✅ | 搜索关键词，逗号分隔。如 `"exchange rate, tail risk"` |
| `--year-start` | 默认2018 | 起始年份 |
| `--year-end` | 默认2025 | 截止年份 |
| `--output` | 默认`./literature_results` | 输出路径前缀（不含扩展名） |
| `--format` | 默认`both` | 输出格式: `xlsx` / `md` / `both` |
| `--json` | 否 | 同时输出 JSON 格式 |
| `--no-dedup` | 否 | 关闭 DOI 去重 |
| `--quiet` | 否 | 静默模式 |

### 方式 B: Python API（适合集成到脚本中）

```python
from scripts.fetcher import search_multi, to_excel, to_markdown

# 搜索文献
df = search_multi(
    journals=["American Economic Review", "Journal of Finance"],
    keywords=["tail risk", "exchange rate"],
    year_start=2020,
    year_end=2025,
)

# 导出
to_excel(df, "results.xlsx")
to_markdown(df, "results.md")
```

### 方式 C: 逐期刊查找 ID + 搜索（最灵活）

```python
from scripts.fetcher import find_source_id, search_journal

sid, name = find_source_id("Journal of Finance")   # → "S5353659", "The Journal of Finance"
results, total = search_journal(sid, "exchange rate", 2020, 2025)
```

## 技术说明

- **数据源**: [OpenAlex](https://openalex.org/) — 完全免费的开放学术图谱 API
- **速率限制**: 无需 API Key，每个请求间隔 0.5s 以保证 polite pool 队列
- **分页**: 游标分页，每页 100 条，自动翻页至全部结果集
- **数据字段**: 年份、作者（前5位）、标题、期刊、卷号、期号、DOI、摘要、搜索关键词、OpenAlex ID
- **摘要**: OpenAlex 的 abstract_inverted_index 会自动反转为正常文本

## 扩展建议

以下是该技能可进一步扩展的方向（如需要可告知）：

1. **中文期刊支持** — 增加 CNKI 知网检索脚本，覆盖中文期刊文献
2. **PDF 链接检测** — 检查每篇文章是否有开放获取的 PDF 版本（通过 Unpaywall API）
3. **引用格式导出** — 增加 BibTeX / RIS / EndNote 格式导出
4. **批量下载检验** — 通过 DOI 批量检查 PDF 的可访问性
5. **文献综述草稿** — 基于检索结果自动生成初版文献综述草稿
6. **关键词扩展** — 根据检索结果中的关键词权重自动推荐扩展检索词

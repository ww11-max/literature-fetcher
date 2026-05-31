# OpenAlex Literature Fetcher

> **[简体中文](README_CN.md) | English**

A free, open-source tool to batch-download academic paper metadata — titles, authors, journals, years, volumes, issues, DOIs, and abstracts.

> **No API key required. Completely free.**
> Perfect for: literature reviews, grant proposal references, thesis preparation, and systematic paper screening.

---

## What It Does

If you are a graduate student or researcher who needs to find papers from specific journals on certain topics, this tool can help:

1. **Search** across multiple journals, keywords, and year ranges at once
2. **Auto-scroll** through all matching papers (no manual pagination)
3. **Extract** year, authors, title, journal, volume, issue, DOI, and abstract from every paper
4. **Deduplicate** — papers matching multiple keywords appear only once
5. **Suggest related keywords** — discover new search terms from the topic labels of your matched papers
6. **Export** results to **Excel** spreadsheets or **Markdown** documents (easy to paste into Word, Notion, or Overleaf)

### A Quick Example

```bash
python scripts/cli.py \
  --journals "Journal of International Economics, Journal of Finance" \
  --keywords "exchange rate, tail risk" \
  --year-start 2020 --year-end 2025 \
  --output ./my_results \
  --json
```

After running, you get:
- `my_results.xlsx` — Open in Excel, filter, sort, search
- `my_results.md` — Literature list with abstracts, ready for your notes
- `my_results.json` — Machine-readable for further processing

---

## Quick Start

### 1. Install Dependencies

Requires Python 3.8 or higher.

```bash
pip install requests pandas openpyxl
```

### 2. Download the Tool

```bash
git clone https://github.com/ww11-max/openalex-literature-fetcher.git
cd openalex-literature-fetcher
```

### 3. Run Your First Search

Search three journals for papers about "tail risk" and "exchange rate" from 2020 to 2025:

```bash
python scripts/cli.py \
  --journals "Journal of International Money and Finance, Journal of International Economics, Journal of Finance" \
  --keywords "tail risk, exchange rate" \
  --year-start 2020 --year-end 2025 \
  --output ./my_literature
```

That's it. The tool will print progress as it searches, then save the results.

---

## Python API (for scripting and automation)

```python
from scripts.fetcher import search_multi, to_excel, to_markdown

# Search
df = search_multi(
    journals=["Journal of International Economics", "Journal of Monetary Economics"],
    keywords=["exchange rate", "financial contagion"],
    year_start=2020,
    year_end=2025,
)

# Export
to_excel(df, "output.xlsx")   # Generates Excel file
to_markdown(df, "output.md")  # Generates Markdown file with year & journal breakdowns
```

### With Keyword Recommendations

```python
df, recs = search_multi(
    journals=["JIMF"],
    keywords=["tail risk"],
    year_start=2024, year_end=2025,
    recommend_kw=True,     # Enable keyword recommendations
    top_n_kw=10,           # Get the top 10 suggestions
)
# recs = [("Currency", 7.0), ("Emerging markets", 6.3), ...]
```

---

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--journals` | **required** | Journal names, comma-separated. E.g. `"AER, JIE, JIMF"` |
| `--keywords` | **required** | Search terms, comma-separated. E.g. `"exchange rate, tail risk"` |
| `--year-start` | 2018 | Start year |
| `--year-end` | 2025 | End year |
| `--output` | `./literature_results` | Output path prefix (without file extension) |
| `--format` | `both` | Output format: `xlsx`, `md`, or `both` |
| `--json` | (flag) | Also export results as JSON |
| `--recommend-keywords` | (flag) | Enable keyword recommendation |
| `--top-n-keywords` | 15 | Number of keywords to recommend |
| `--no-dedup` | (flag) | Skip deduplication (not recommended) |
| `--quiet` | (flag) | Suppress progress output |

---

## Output Fields

| Column | Description |
|--------|-------------|
| 年份 (Year) | Publication year |
| 作者 (Authors) | Author names, semicolon-separated (up to 5) |
| 标题 (Title) | Paper title |
| 期刊 (Journal) | Journal name |
| 卷号 (Volume) | Journal volume |
| 期号 (Issue) | Journal issue |
| DOI | Digital Object Identifier (link to the paper) |
| 摘要 (Abstract) | Paper abstract |
| 搜索关键词 (Search Term) | Which keyword matched this paper |
| OpenAlex ID | Unique ID in the OpenAlex database |

---

## How It Works

1. **Journal lookup** — Each journal name is resolved to an OpenAlex Source ID via the `/sources` endpoint
2. **Search** — For every journal+keyword combination, call the `/works` API with year range filter
3. **Pagination** — Uses cursor-based pagination (100 results per page), fetches all pages automatically
4. **Extraction** — Parses year, authors, title, journal, volume, issue, DOI, and abstract from each result
5. **Deduplication** — Removes papers with the same DOI across all queries
6. **Keyword recommendation** — Aggregates OpenAlex's topic labels across all fetched papers, ranks by weighted relevance score
7. **Export** — Writes to Excel (.xlsx), Markdown (.md), and/or JSON (.json)

### Data Source

All data comes from [OpenAlex](https://openalex.org/) — a fully free and open index of hundreds of millions of scholarly works, complete with metadata, citations, and author information.

---

## License

MIT

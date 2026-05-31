# OpenAlex Literature Fetcher

Batch download academic paper metadata (title, authors, journal, year, volume, issue, DOI, abstract) from [OpenAlex](https://openalex.org/) — a free and open academic graph API.

> **No API key required.** OpenAlex is completely free.
> Suitable for literature review, grant proposal reference collection, and research discovery.

## Features

- **Batch search** — Multiple journals × multiple keywords × any year range
- **Auto pagination** — Fetches all results (cursor-based, 100 per page)
- **Metadata extraction** — Title, authors, journal, year, volume, issue, DOI, abstract
- **Deduplication** — Unique papers by DOI across overlapping keyword queries
- **Keyword recommendation** — Suggests related keywords from OpenAlex's topic model
- **Multi-format export** — XLSX, Markdown, and JSON

## Quick Start

```bash
# Search with CLI
python scripts/cli.py \
  --journals "Journal of International Economics, Journal of Finance" \
  --keywords "exchange rate, tail risk" \
  --year-start 2020 --year-end 2025 \
  --output ./my_results \
  --json

# Enable keyword recommendations
python scripts/cli.py \
  --journals "American Economic Review" \
  --keywords "monetary policy, spillover" \
  --year-start 2023 --year-end 2025 \
  --output ./results \
  --recommend-keywords
```

## Python API

```python
from scripts.fetcher import search_multi, to_excel, to_markdown, find_source_id

# Find a journal's OpenAlex ID
sid, name = find_source_id("Journal of Political Economy")
# sid = "S95323914", name = "Journal of Political Economy"

# Batch search
df = search_multi(
    journals=["Journal of International Economics", "Journal of Monetary Economics"],
    keywords=["exchange rate", "financial contagion"],
    year_start=2020,
    year_end=2025,
)

# Export
to_excel(df, "output.xlsx")
to_markdown(df, "output.md")

# With keyword recommendations
df, recs = search_multi(
    journals=["JIMF"],
    keywords=["tail risk", "forex"],
    year_start=2024, year_end=2025,
    recommend_kw=True,
    top_n_kw=10,
)
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--journals` | (required) | Journal names, comma-separated |
| `--keywords` | (required) | Search keywords, comma-separated |
| `--year-start` | 2018 | Start year |
| `--year-end` | 2025 | End year |
| `--output` | `./literature_results` | Output path prefix |
| `--format` | `both` | Output format: `xlsx`, `md`, or `both` |
| `--json` | (flag) | Also export as JSON |
| `--recommend-keywords` | (flag) | Enable keyword recommendation |
| `--top-n-keywords` | 15 | Number of keywords to recommend |
| `--no-dedup` | (flag) | Skip deduplication |
| `--quiet` | (flag) | Suppress progress output |

## Output Fields

| Field | Description |
|-------|-------------|
| 年份 (Year) | Publication year |
| 作者 (Authors) | Author names, semicolon-separated (up to 5) |
| 标题 (Title) | Paper title |
| 期刊 (Journal) | Journal name |
| 卷号 (Volume) | Journal volume |
| 期号 (Issue) | Journal issue |
| DOI | Digital Object Identifier |
| 摘要 (Abstract) | Paper abstract |
| 搜索关键词 (Search Term) | Keyword that matched this paper |
| OpenAlex ID | OpenAlex paper ID |

## How It Works

1. **Journal lookup** — Each journal name is resolved to an OpenAlex Source ID via `/sources` endpoint
2. **Search** — For each journal+keyword pair, calls `/works` with `filter` (source ID + year range) and `search`
3. **Pagination** — Uses OpenAlex's cursor-based pagination (100 results per page)
4. **Extraction** — Parses `primary_location`, `authorships`, `biblio`, `abstract_inverted_index`
5. **Recommendation** — Aggregates the `keywords` field across all fetched works, ranks by weighted score
6. **Export** — Writes to XLSX, Markdown, and/or JSON

## Dependencies

- Python ≥ 3.8
- `requests` — HTTP client
- `pandas` — Data manipulation
- `openpyxl` — XLSX export (installed with pandas)

```bash
pip install requests pandas openpyxl
```

## License

MIT

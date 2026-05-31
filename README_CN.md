# Literature Fetcher

> **简体中文 | [English](README.md)**

批量获取学术论文元数据（标题、作者、期刊、年份、卷期号、DOI、摘要）的开源工具。

> **无需 API 密钥，完全免费。**
> 适合：写文献综述、整理参考文献、开题报告、课题申报时的文献检索。

---

## 它能做什么？

你是一个研究生或科研人员，需要从一批指定期刊中搜特定主题的论文。这个工具可以：

1. 按**期刊名** + **关键词** + **年份范围** 批量搜索学术论文
2. 自动翻页，把符合条件的论文全部抓下来
3. 提取每篇论文的发表年份、作者、标题、期刊、卷号、期号、DOI、摘要
4. **去重**——同一个关键词搜出来的论文不会重复
5. **推荐扩展关键词**——告诉你还可以搜哪些相关词来补充文献
6. 输出为 **Excel** 表格或 **Markdown** 文档（方便复制到 Word 或 Notion）

### 举个例子

```bash
python scripts/cli.py \
  --journals "Journal of International Economics, Journal of Finance" \
  --keywords "汇率, 尾部风险" \
  --year-start 2020 --year-end 2025 \
  --output ./我的检索结果 \
  --json
```

执行后，你会得到：
- `我的检索结果.xlsx` — 可以直接在 Excel 中打开，筛选、排序
- `我的检索结果.md` — 带摘要的文献列表，适合贴到笔记里
- `我的检索结果.json` — 适合程序进一步处理

---

## 快速上手 — 配合AI助手使用

这个工具专门设计给 Claude、Codex、OpenClaw 等终端型 AI 编程助手调用。你只需要告诉 AI 你要什么文献，AI 就会自动运行这个工具帮你搜。

### 1. 安装依赖

需要 Python 3.8 或更高版本。

```bash
pip install requests pandas openpyxl
```

### 2. 下载工具

```bash
git clone https://github.com/ww11-max/literature-fetcher.git
cd literature-fetcher
```

### 3. 在 AI 助手中调用

告诉 AI 工具的路径，然后描述你的检索需求即可。以下是几个示例：

**在 Claude Code 中：**
```
我有一个文献检索工具，路径在 ./literature-fetcher/scripts/cli.py。
帮我搜 Journal of International Economics 和 JIMF 这两个期刊上，
2020年到2025年间关于"exchange rate"和"tail risk"的论文，
输出到 ./my_results。
```

**在 Codex / Windsurf / Cursor 中：**
```
帮我执行: python literature-fetcher/scripts/cli.py \
  --journals "Journal of International Economics, JIMF" \
  --keywords "exchange rate, tail risk" \
  --year-start 2020 --year-end 2025 \
  --output ./my_results
```

**在 OpenClaw 或其他 MCP 终端代理中：**
```
工具路径: python literature-fetcher/scripts/cli.py
参数: --journals "JIMF, AER" --keywords "monetary policy, spillover"
      --year-start 2023 --year-end 2025 --output ./results
```

### 4. 一句命令直达

下载完成后，你也可以直接让 AI 跑这一行：

```bash
python ./literature-fetcher/scripts/cli.py \
  --journals "Journal of International Money and Finance, Journal of International Economics, Journal of Finance" \
  --keywords "tail risk, exchange rate, financial contagion" \
  --year-start 2020 --year-end 2025 \
  --output ./my_literature \
  --json --recommend-keywords
```

执行后你会得到：
- `my_literature.xlsx` — 可直接用 Excel 打开
- `my_literature.md` — 带摘要的文献列表
- `my_literature.json` — 机器可读的数据
- `my_literature_keyword_recommendations.md` — 推荐的新搜索词

---

## Python API（适合嵌入到自己的脚本中）

```python
from scripts.fetcher import search_multi, to_excel, to_markdown

# 搜索
df = search_multi(
    journals=["Journal of International Economics", "Journal of Monetary Economics"],
    keywords=["exchange rate", "financial contagion"],
    year_start=2020,
    year_end=2025,
)

# 导出
to_excel(df, "output.xlsx")   # 生成 Excel
to_markdown(df, "output.md")  # 生成 Markdown（含年份分布和期刊统计）
```

### 启用关键词推荐

```python
df, recs = search_multi(
    journals=["JIMF"],
    keywords=["tail risk"],
    year_start=2024, year_end=2025,
    recommend_kw=True,      # 开启关键词推荐
    top_n_kw=10,            # 推荐前10个
)
# recs = [("Currency", 7.0), ("Emerging markets", 6.3), ...]
```

---

## 命令行参数一览

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--journals` | **必填** | 期刊名称，多个用逗号分隔。如 `"AER, JIE, JIMF"` |
| `--keywords` | **必填** | 搜索关键词，多个用逗号分隔。如 `"exchange rate, tail risk"` |
| `--year-start` | 2018 | 起始年份 |
| `--year-end` | 2025 | 截止年份 |
| `--output` | `./literature_results` | 输出文件的路径前缀（不含扩展名） |
| `--format` | `both` | 输出格式：`xlsx`（仅Excel）、`md`（仅Markdown）、`both`（两种） |
| `--json` | 无 | 加上此参数额外输出 JSON 文件 |
| `--recommend-keywords` | 无 | 加上此参数开启关键词推荐功能 |
| `--top-n-keywords` | 15 | 推荐多少个关键词 |
| `--no-dedup` | 无 | 加上此参数关闭去重（不推荐） |
| `--quiet` | 无 | 加上此参数不输出进度信息 |

---

## 输出文件包含哪些字段？

| 字段名 | 含义 |
|--------|------|
| 年份 | 论文发表年份 |
| 作者 | 作者姓名（分号分隔，最多显示5位） |
| 标题 | 论文标题 |
| 期刊 | 期刊名称 |
| 卷号 | 期刊卷号 |
| 期号 | 期刊期号 |
| DOI | 论文的数字对象标识符（可直接用此链接访问论文页面） |
| 摘要 | 论文摘要 |
| 搜索关键词 | 本次搜索匹配的关键词（方便你知道这篇是从哪个关键词搜到的） |
| OpenAlex ID | OpenAlex 数据库中的唯一标识 |

---

## 技术原理（简要版）

1. **查找期刊** — 工具先把输入的期刊名称转换成 OpenAlex 内部的 Source ID
2. **搜索文献** — 对每个期刊+关键词的组合，调用 OpenAlex 的 `/works` API
3. **翻页** — 用游标分页，每页 100 条，自动翻到最后一页
4. **提取信息** — 从每条结果中提取年份、作者、标题、期刊、卷期、DOI、摘要
5. **去重** — 按 DOI 去掉重复的论文
6. **关键词推荐** — 把 OpenAlex 给每篇论文标注的关键词汇总起来，按权重排序
7. **导出** — 写入 Excel / Markdown / JSON 文件

### 数据来源

所有数据来自 [OpenAlex](https://openalex.org/)——一个完全免费的开放学术图谱，覆盖数亿篇学术论文的元数据、引文关系、作者信息等。

---

## 许可证

MIT

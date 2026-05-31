#!/usr/bin/env python3
"""
OpenAlex Literature Fetcher — 学术文献元数据批量获取工具

功能：
- 按期刊名+关键词+年份范围，通过 OpenAlex API 批量搜索文献
- 自动翻页获取全部结果，提取标题/作者/期刊/卷期/DOI/摘要
- 支持多个期刊和多个关键词的组合搜索
- 关键词推荐：从检索结果中聚合 OpenAlex 标注的关键词，按权重排序推荐扩展检索词
- 输出 XLSX 和 Markdown 两种格式
"""
import requests, time, re, sys, os, json
import pandas as pd
from collections import OrderedDict

# ============================================================
# 配置
# ============================================================
BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 100

# ============================================================
# 核心函数
# ============================================================

def find_source_id(journal_name):
    """通过期刊名称查找 OpenAlex source ID（自动）

    Args:
        journal_name: 期刊名称（完整或部分）
    Returns:
        (source_id, display_name) 或 (None, None)
    """
    url = f"https://api.openalex.org/sources?search={requests.utils.quote(journal_name)}&per-page=5&mailto=academic-research@example.com"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return None, None
        best = None
        for s in r.json().get("results", []):
            dn = s["display_name"].lower().strip()
            jn = journal_name.lower().strip()
            # 优先精确匹配
            if dn == jn:
                return s["id"].replace("https://openalex.org/", ""), s["display_name"]
            # 次选包含匹配
            if jn in dn or dn in jn:
                best = (s["id"].replace("https://openalex.org/", ""), s["display_name"])
        return best if best else (None, None)
    except:
        return None, None


def search_journal(source_id, keyword, year_start, year_end, max_pages=None):
    """搜索单个期刊的文献，自动翻页

    Args:
        source_id: OpenAlex source ID (如 S23254222)
        keyword: 搜索关键词
        year_start: 起始年份
        year_end: 截止年份
        max_pages: 最大翻页数（None=不限）
    Returns:
        (results_list, total_count)
    """
    results = []
    raw_keywords = []  # 收集每篇文章的keywords，供后续推荐用
    cursor = "*"
    page = 0

    while max_pages is None or page < max_pages:
        params = OrderedDict([
            ("filter", f"primary_location.source.id:{source_id},publication_year:{year_start}-{year_end}"),
            ("search", keyword),
            ("per-page", PER_PAGE),
            ("cursor", cursor),
            ("mailto", "academic-research@example.com"),
        ])
        try:
            r = requests.get(BASE_URL, params=params, timeout=30)
            if r.status_code != 200:
                break
            d = r.json()
            works = d.get("results", [])
            meta = d.get("meta", {})
            cursor = meta.get("next_cursor")
            if not works:
                break
            for w in works:
                rec = _extract_work(w)
                rec["搜索关键词"] = keyword
                results.append(rec)
                # 收集keywords
                paper_kws = w.get("keywords", [])
                raw_keywords.extend(paper_kws)
            page += 1
            if not cursor:
                break
            time.sleep(0.5)
        except:
            break

    return results, meta.get("count", 0) if meta else (len(results) if results else 0), raw_keywords


def search_multi(journals, keywords, year_start, year_end, dedup=True, verbose=True,
                 recommend_kw=False, top_n_kw=15):
    """批量搜索多个期刊 × 多个关键词

    Args:
        journals: 期刊列表，每一项为 (期刊名, source_id) 或直接传期刊名（自动调 source_id）
        keywords: 关键词列表
        year_start: 起始年份
        year_end: 截止年份
        dedup: 是否按DOI去重
        verbose: 是否打印进度
        recommend_kw: 是否返回关键词推荐结果
        top_n_kw: 推荐关键词数量
    Returns:
        DataFrame (以及可选的 keyword_recommendations 字典)
    """
    all_works = []
    all_raw_keywords = []
    journal_map = {}

    # 解析期刊输入
    for j in journals:
        if isinstance(j, str):
            journal_map[j] = None
        elif isinstance(j, (list, tuple)):
            journal_map[j[0]] = j[1]

    for jn in journal_map:
        sid = journal_map[jn]
        if not sid:
            if verbose:
                print(f"[查找] {jn} 的 OpenAlex ID...", end=" ")
            sid, disp = find_source_id(jn)
            if not sid:
                if verbose:
                    print("✗ 未找到")
                continue
            if verbose:
                print(f"✓ {disp} ({sid})")
            journal_map[jn] = sid

    for jn, sid in journal_map.items():
        if not sid:
            continue
        if verbose:
            print(f"\n▶ {jn}")
        for kw in keywords:
            res, total, kw_list = search_journal(sid, kw, year_start, year_end)
            all_works.extend(res)
            all_raw_keywords.extend(kw_list)
            if verbose:
                kw_show = kw[:30].ljust(32)
                print(f"  [{kw_show}] 总{total:>5} | 取{len(res):>4}条")
            time.sleep(0.3)

    # 去重
    df = pd.DataFrame(all_works)
    if df.empty:
        return (df, {}) if recommend_kw else df
    if dedup and "DOI" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset="DOI", keep="first")
        if verbose:
            print(f"\n去重: {before} → {len(df)} 条")

    result = df
    if recommend_kw:
        recs = _compute_keyword_recommendations(all_raw_keywords, top_n_kw)
        if verbose:
            print(f"\n关键词推荐:")
            for kw_name, score in recs[:12]:
                print(f"  {kw_name:<35s} score={score:.3f}")
        return df, recs

    return df


def _extract_work(w):
    """从 OpenAlex work 对象提取元数据"""
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    bib = w.get("biblio") or {}
    authors = "; ".join(
        (a.get("author") or {}).get("display_name", "")
        for a in (w.get("authorships") or [])
        if (a.get("author") or {}).get("display_name")
    )[:300]
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    abstract = _invert_abstract(w.get("abstract_inverted_index", ""))
    return {
        "年份": w.get("publication_year", ""),
        "作者": authors,
        "标题": (w.get("title") or "").replace("\n", " ").strip(),
        "期刊": src.get("display_name", ""),
        "卷号": bib.get("volume", ""),
        "期号": bib.get("issue", ""),
        "DOI": doi,
        "摘要": abstract,
        "OpenAlex ID": (w.get("id") or "").replace("https://openalex.org/", ""),
    }


def _invert_abstract(inverted):
    """将 OpenAlex 反序索引摘要转换为正常文本"""
    if not inverted:
        return ""
    if isinstance(inverted, str):
        return inverted
    try:
        words = [(pos, w) for w, positions in inverted.items() for pos in positions]
        words.sort(key=lambda x: x[0])
        return " ".join(w for _, w in words)
    except:
        return str(inverted)


# ============================================================
# 导出函数
# ============================================================

def _compute_keyword_recommendations(raw_keywords, top_n=15):
    """从 OpenAlex 的 keywords 字段中聚合推荐关键词

    Args:
        raw_keywords: OpenAlex API 返回的 keywords 列表（每项含 display_name, score）
        top_n: 推荐数量
    Returns:
        按总权重降序排列的 [(keyword_name, aggregated_score), ...]
    """
    from collections import defaultdict
    agg = defaultdict(lambda: {"score_sum": 0.0, "count": 0})

    for kw in raw_keywords:
        name = kw.get("display_name", "")
        score = kw.get("score", 0)
        if name and name.lower() not in ("exchange rate", "monetary policy"):
            agg[name]["score_sum"] += score
            agg[name]["count"] += 1

    # 排序：总权重 × 出现次数
    ranked = [
        (name, round(v["score_sum"], 3))
        for name, v in agg.items()
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def recommend_keywords_from_df(df, top_n=15):
    """从已有 DataFrame 的标题和摘要中提取高频词作为推荐

    当 OpenAlex API 未返回 keywords 字段时，可用此方法补救。
    基于简单的 TF 统计，返回高频词列表。

    Args:
        df: 包含"标题"和"摘要"列的 DataFrame
        top_n: 推荐数量
    Returns:
        [(keyword, count), ...]
    """
    import re
    from collections import Counter

    stop_words = {
        "the", "a", "an", "of", "in", "to", "and", "is", "for", "that", "on",
        "this", "with", "we", "are", "as", "by", "be", "from", "or", "at",
        "it", "not", "but", "has", "have", "do", "does", "its", "their",
        "our", "will", "was", "were", "been", "which", "can", "may",
        "研究", "分析", "影响", "基于", "我国", "一个", "中国", "问题",
        "方法", "数据", "模型", "结果", "本文", "不同", "进行", "发现",
    }

    text = ""
    for c in ["标题", "摘要"]:
        if c in df.columns:
            text += " ".join(df[c].dropna().astype(str)) + " "

    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    words += re.findall(r"[\u4e00-\u9fff]{2,4}", text)

    counter = Counter(w for w in words if w not in stop_words)
    return counter.most_common(top_n)

def to_excel(df, output_path):
    """导出为 XLSX"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_excel(output_path, index=False, sheet_name="文献列表")
    return output_path


def to_markdown(df, output_path):
    """导出为 Markdown 表格"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 文献检索结果\n\n")
        f.write(f"- 检索时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"- 共 {len(df)} 篇文献\n\n")

        # 按年份分组摘要
        if "年份" in df.columns:
            year_counts = df["年份"].value_counts().sort_index(ascending=False)
            f.write("### 年份分布\n\n")
            for y, c in year_counts.items():
                f.write(f"- {y}: {c}篇\n")
            f.write("\n")

        if "期刊" in df.columns:
            journal_counts = df["期刊"].value_counts()
            f.write("### 期刊分布\n\n")
            for j, c in journal_counts.items():
                f.write(f"- {j}: {c}篇\n")
            f.write("\n")

        # 详细列表
        f.write("### 详细列表\n\n")
        cols = [c for c in ["年份", "作者", "标题", "期刊", "卷号", "期号", "DOI", "摘要"] if c in df.columns]
        f.write("| " + " | ".join(cols) + " |\n")
        f.write("| " + " | ".join(["---"] * len(cols)) + " |\n")

        for _, row in df.iterrows():
            vals = []
            for c in cols:
                v = str(row.get(c, ""))[:80].replace("\n", " ").replace("|", "\\|")
                vals.append(v)
            f.write("| " + " | ".join(vals) + " |\n")
    return output_path

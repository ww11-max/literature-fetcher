#!/usr/bin/env python3
"""
CLI入口 — 可直接被终端调用，也适合被 AI agent 调用。
用法:
  python cli.py --journals "AER, JIE, JIMF" --keywords "exchange rate, monetary policy" \
                --year-start 2020 --year-end 2025 --output ./results
"""
import argparse, sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from fetcher import search_multi, to_excel, to_markdown, find_source_id


def parse_list(text):
    items = [x.strip() for x in text.split(",") if x.strip()]
    return items


def main():
    parser = argparse.ArgumentParser(description="OpenAlex 文献元数据批量获取工具")
    parser.add_argument("--journals", required=True, help="期刊名，逗号分隔")
    parser.add_argument("--keywords", required=True, help="关键词，逗号分隔")
    parser.add_argument("--year-start", type=int, default=2018, help="起始年份")
    parser.add_argument("--year-end", type=int, default=2025, help="截止年份")
    parser.add_argument("--output", default="./literature_results", help="输出路径前缀")
    parser.add_argument("--no-dedup", action="store_true", help="不去重")
    parser.add_argument("--format", choices=["xlsx", "md", "both"], default="both", help="输出格式")
    parser.add_argument("--json", action="store_true", help="同时输出 JSON 格式")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    parser.add_argument("--recommend-keywords", action="store_true", help="启用关键词推荐")
    parser.add_argument("--top-n-keywords", type=int, default=15, help="推荐关键词数量")

    args = parser.parse_args()

    journals = parse_list(args.journals)
    keywords = parse_list(args.keywords)
    output_prefix = args.output.rstrip(".xlsx").rstrip(".md").rstrip(".json")
    os.makedirs(os.path.dirname(output_prefix) or ".", exist_ok=True)

    # 获取期刊 OpenAlex ID
    sids = []
    if not args.quiet:
        print(f"Journals: {', '.join(journals)}")
        print(f"Keywords: {', '.join(keywords)}")
        print(f"Year range: {args.year_start}-{args.year_end}")
    for j in journals:
        sid, disp = find_source_id(j)
        if sid:
            sids.append((j, sid, disp))
            if not args.quiet:
                print(f"  {j} -> {disp} ({sid})")
        else:
            print(f"  {j} -> NOT FOUND")
            return 1
        time.sleep(0.3)
    if not args.quiet:
        print()

    journal_inputs = [(j, sid) for j, sid, _ in sids]

    if args.recommend_keywords:
        df, kw_recs = search_multi(
            journals=journal_inputs,
            keywords=keywords,
            year_start=args.year_start,
            year_end=args.year_end,
            dedup=not args.no_dedup,
            verbose=not args.quiet,
            recommend_kw=True,
            top_n_kw=args.top_n_keywords,
        )
    else:
        df = search_multi(
            journals=journal_inputs,
            keywords=keywords,
            year_start=args.year_start,
            year_end=args.year_end,
            dedup=not args.no_dedup,
            verbose=not args.quiet,
        )

    if df.empty:
        print("\nNo papers found.")
        return 0

    print(f"\nTotal: {len(df)} papers")

    out_files = []

    if args.format in ("xlsx", "both"):
        path = f"{output_prefix}.xlsx"
        to_excel(df.copy(), path)
        out_files.append(path)
        if not args.quiet:
            print(f"  XLSX: {path}")

    if args.format in ("md", "both"):
        path = f"{output_prefix}.md"
        to_markdown(df.copy(), path)
        out_files.append(path)
        if not args.quiet:
            print(f"  MD: {path}")

    if args.json:
        path = f"{output_prefix}.json"
        df.to_json(path, orient="records", force_ascii=False, indent=2)
        out_files.append(path)
        if not args.quiet:
            print(f"  JSON: {path}")

    # 关键词推荐单独输出
    if args.recommend_keywords and kw_recs:
        rec_path = f"{output_prefix}_keyword_recommendations.md"
        with open(rec_path, "w", encoding="utf-8") as f:
            f.write("# Keyword Recommendations\n\n")
            f.write(f"Based on {len(df)} papers, top {len(kw_recs)} keywords:\n\n")
            f.write("| Rank | Keyword | Score |\n|------|---------|-------|\n")
            for i, (kw, sc) in enumerate(kw_recs, 1):
                f.write(f"| {i} | {kw} | {sc} |\n")
        out_files.append(rec_path)
        if not args.quiet:
            print(f"  Keyword Recs: {rec_path}")

    print(f"\nOutput files ({len(out_files)}):")
    for f in out_files:
        print(f"  {f}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)

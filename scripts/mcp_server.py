#!/usr/bin/env python3
"""
MCP Server for Literature Fetcher — 让 Claude Code / Codex / OpenClaw 等 AI 工具
通过 MCP 协议直接调用文献检索功能。
"""
import sys, json, os

# 将 scripts 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fetcher import search_multi, to_excel, to_markdown, find_source_id


def handle_request(req):
    """处理 MCP JSON-RPC 请求"""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_papers",
                        "description": "批量搜索学术论文元数据（标题、作者、期刊、年份、卷期、DOI、摘要）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "journals": {
                                    "type": "string",
                                    "description": "期刊名称，多个用逗号分隔。例: 'Journal of International Economics, Journal of Finance'"
                                },
                                "keywords": {
                                    "type": "string",
                                    "description": "搜索关键词，多个用逗号分隔。例: 'exchange rate, tail risk'"
                                },
                                "year_start": {
                                    "type": "integer",
                                    "description": "起始年份，默认 2018"
                                },
                                "year_end": {
                                    "type": "integer",
                                    "description": "截止年份，默认 2025"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录，默认当前目录"
                                },
                                "recommend_keywords": {
                                    "type": "boolean",
                                    "description": "是否推荐扩展关键词，默认 false"
                                }
                            },
                            "required": ["journals", "keywords"]
                        }
                    },
                    {
                        "name": "lookup_journal",
                        "description": "查找期刊的 OpenAlex ID",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "journal_name": {
                                    "type": "string",
                                    "description": "期刊名称"
                                }
                            },
                            "required": ["journal_name"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "search_papers":
            return handle_search(req_id, args)
        elif tool_name == "lookup_journal":
            return handle_lookup(req_id, args)
        else:
            return error(req_id, -32601, f"Unknown tool: {tool_name}")

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "literature-fetcher",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    else:
        return error(req_id, -32601, f"Method not found: {method}")


def handle_search(req_id, args):
    journals = [j.strip() for j in args.get("journals", "").split(",") if j.strip()]
    keywords = [k.strip() for k in args.get("keywords", "").split(",") if k.strip()]
    year_start = args.get("year_start", 2018)
    year_end = args.get("year_end", 2025)
    output_dir = args.get("output_dir", ".")
    recommend = args.get("recommend_keywords", False)

    if not journals or not keywords:
        return error(req_id, -32602, "journals 和 keywords 不能为空")

    os.makedirs(output_dir, exist_ok=True)
    output_prefix = os.path.join(output_dir, "literature_results")

    # 解析期刊 ID
    sids = []
    msgs = []
    for j in journals:
        sid, disp = find_source_id(j)
        if sid:
            sids.append((j, sid))
            msgs.append(f"✓ {j} → {disp}")
        else:
            msgs.append(f"✗ {j} → 未找到")
        import time; time.sleep(0.3)

    if not sids:
        return error(req_id, -32602, "所有期刊均未找到，请检查期刊名称")

    # 搜索
    if recommend:
        df, kw_recs = search_multi(
            journals=sids, keywords=keywords,
            year_start=year_start, year_end=year_end,
            recommend_kw=True, verbose=False,
        )
    else:
        df = search_multi(
            journals=sids, keywords=keywords,
            year_start=year_start, year_end=year_end,
            verbose=False,
        )

    if df.empty:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{
                    "type": "text",
                    "text": "未找到匹配的文献。\n" + "\n".join(msgs)
                }]
            }
        }

    # 导出
    xlsx_path = to_excel(df.copy(), f"{output_prefix}.xlsx")
    md_path = to_markdown(df.copy(), f"{output_prefix}.md")

    summary = (
        f"✅ 共找到 {len(df)} 篇文献\n\n"
        f"**检索条件**\n"
        f"- 期刊: {', '.join(journals)}\n"
        f"- 关键词: {', '.join(keywords)}\n"
        f"- 年份: {year_start}-{year_end}\n\n"
        f"**输出文件**\n"
        f"- 📊 Excel: {xlsx_path}\n"
        f"- 📝 Markdown: {md_path}\n"
    )

    if recommend and kw_recs:
        rec_path = f"{output_prefix}_keyword_recommendations.md"
        with open(rec_path, "w", encoding="utf-8") as f:
            f.write("# 关键词推荐\n\n")
            for i, (kw, sc) in enumerate(kw_recs, 1):
                f.write(f"{i}. {kw} (score: {sc})\n")
        summary += f"- 🔑 关键词推荐: {rec_path}\n"
        summary += "\n**推荐扩展关键词**\n"
        for kw, sc in kw_recs[:8]:
            summary += f"- {kw}\n"

    # 前5条摘要
    summary += "\n**前5条结果预览**\n"
    for _, row in df.head(5).iterrows():
        title = str(row.get("标题", ""))[:80]
        year = row.get("年份", "")
        authors = str(row.get("作者", ""))[:40]
        summary += f"- [{year}] {title} ({authors})\n"

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [{"type": "text", "text": summary}]
        }
    }


def handle_lookup(req_id, args):
    name = args.get("journal_name", "")
    if not name:
        return error(req_id, -32602, "journal_name 不能为空")
    sid, disp = find_source_id(name)
    if sid:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"{name} → {disp} (ID: {sid})"}]
            }
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"未找到期刊: {name}"}]
            }
        }


def error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message}
    }


def main():
    """MCP Server 主循环：从 stdin 读取 JSON-RPC，输出到 stdout"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line.strip())
            resp = handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except EOFError:
            break


if __name__ == "__main__":
    main()

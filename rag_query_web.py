#!/usr/bin/env python3
"""Minimal RAG query server using only stdlib."""
import html
import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add langchain-llm-toolkit to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>知识库查询</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:800px;margin:40px auto;padding:0 20px}
h1{margin-bottom:24px;color:#111}
form{display:flex;gap:8px;margin-bottom:24px}
input{flex:1;padding:10px 16px;font-size:15px;border:1px solid #d1d5db;border-radius:8px}
button{padding:10px 24px;background:#111;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:15px}
button:hover{background:#333}
.result{border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:12px}
.result .meta{font-size:12px;color:#9ca3af;margin-bottom:8px}
.result pre{font-size:14px;color:#374151;line-height:1.7;white-space:pre-wrap;max-height:300px;overflow-y:auto;font-family:inherit}
.hint{color:#9ca3af;font-size:13px;margin-top:16px}
.loading{color:#6b7280;font-size:14px}
</style></head><body>
<h1>📚 个人知识库查询</h1>
<form method="GET">
<input type="text" name="q" placeholder="输入查询..." value="{query}">
<button type="submit">查询</button>
</form>
{results}
<div class="hint">65 篇文档 · 投资策略 · 财务分析 · 数字分身</div>
</body></html>"""

RESULT_TMPL = '<div class="result"><div class="meta">📁 {cat} | {src}</div><pre>{content}</pre></div>'


def search_knowledge(query, k=5):
    from langchain_llm_toolkit.rag import RAGSystem
    from langchain_ollama import OllamaEmbeddings

    vs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store")
    rag = RAGSystem(vector_store_type="faiss", embedding_type="ollama", embedding_model="nomic-embed-text:latest")
    rag.embeddings = OllamaEmbeddings(model="nomic-embed-text:latest", base_url="http://localhost:11434")
    rag.faiss_persist_dir = vs
    rag.load_vector_store()
    return rag.retrieve_hybrid(query, k=k, bm25_weight=0.3)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        query = params.get("q", [""])[0].strip()
        results_html = ""

        if query:
            try:
                docs = search_knowledge(query, k=5)
                for d in docs:
                    results_html += RESULT_TMPL.format(
                        cat=html.escape(d.metadata.get("category", "?")),
                        src=html.escape(d.metadata.get("source", "?")),
                        content=html.escape(d.page_content[:1200]),
                    )
            except Exception as e:
                results_html = f'<div class="result"><pre>{html.escape(str(e))}</pre></div>'

        page = HTML.replace("{query}", html.escape(query)).replace("{results}", results_html)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Suppress logs


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8502
    print(f"http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

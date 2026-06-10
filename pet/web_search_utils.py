"""
联网搜索模块 — 让 Rick 能实时搜索网络信息。
支持 DuckDuckGo、Bing 等多后端，用于拓展 LLM 对话的知识范围。
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional


class WebSearchUtils:
    """联网搜索工具。

    当 LLM 需要最新信息时，Rick 可以使用此模块搜索网络。
    支持多个后端，自动 fallback。
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def search_duckduckgo(self, query: str, max_results: int = 5) -> list:
        """通过 DuckDuckGo HTML 搜索"""
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            # 简单解析搜索结果
            import re
            # 提取标题和链接
            titles = re.findall(r'class="result__title">.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
            snippets = re.findall(r'class="result__snippet">(.*?)</a>', html, re.DOTALL)
            links = re.findall(r'class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)
            # 备用：提取所有链接
            if not links:
                links = re.findall(r'uddg=(https?://[^&\'"]+)', html)

            for i in range(min(len(titles), max_results)):
                title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
                snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                url_link = urllib.parse.unquote(links[i]) if i < len(links) else ""
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": url_link,
                })
        except Exception:
            pass
        return results

    def search_bing(self, query: str, max_results: int = 5) -> list:
        """通过 Bing 搜索"""
        results = []
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            import re
            # 提取搜索结果
            items = re.findall(
                r'<li class="b_algo"[^>]*>.*?<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<p[^>]*>(.*?)</p>',
                html, re.DOTALL
            )
            for href, title_html, snippet_html in items[:max_results]:
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet_html).strip()
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": href,
                })
        except Exception:
            pass
        return results

    def search(self, query: str, max_results: int = 5) -> list:
        """综合搜索（尝试多个后端，返回第一个成功的结果）"""
        # 优先 DuckDuckGo
        results = self.search_duckduckgo(query, max_results)
        if results:
            return results
        # Fallback Bing
        results = self.search_bing(query, max_results)
        return results

    def search_for_llm(self, query: str, max_results: int = 3) -> str:
        """搜索并将结果格式化为 LLM 可用的上下文"""
        results = self.search(query, max_results)
        if not results:
            return ""

        lines = ["[Web search results for: " + query + "]"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            if r['snippet']:
                lines.append(f"   {r['snippet'][:200]}")
        return "\n".join(lines)


# 简易内嵌搜索：用于在 Rick 语录和知识库中查找
RICK_KNOWLEDGE = {
    "portal gun": "The Portal Gun creates interdimensional portals. It runs on a miniature black hole and can travel to any dimension in the multiverse.",
    "plumbus": "A Plumbus is a common household item used for... things. Everyone has one. It's made from dinglebop, schleem, grumbo, and fleeb juice.",
    "meeseeks": "Meeseeks are creatures summoned by a Meeseeks Box. They exist only to complete one task, and existence is pain for them.",
    "pickle rick": "Pickle Rick is the result of Rick turning himself into a pickle to avoid family therapy. He built an exoskeleton from rat parts.",
    "microverse": "A microverse is a miniature universe contained inside a battery. The inhabitants unknowingly generate power by stepping on gooble boxes.",
    "schwifty": "Getting Schwifty means letting loose and having a good time. It involves a specific dance and the song 'Get Schwifty'.",
    "dimension c-137": "Dimension C-137 is the original dimension of our Rick. It was destroyed, and Rick now lives with the Smith family of another dimension.",
    "vindicators": "The Vindicators are a superhero team. Rick despises them and once turned their base into a Saw-like trap.",
    "birdperson": "Birdperson is Rick's best friend from the rebellion against the Galactic Federation. His catchphrase is 'In bird culture, this is considered a dick move.'",
    "szechuan sauce": "Rick's entire character motivation in Season 3 was to get McDonald's Szechuan Sauce, a limited-edition 1998 tie-in for the movie Mulan.",
}

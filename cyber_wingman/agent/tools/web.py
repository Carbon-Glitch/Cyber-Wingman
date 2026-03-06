"""
Web 工具 — 搜索和网页抓取。

提供:
- web_search: Tavily（主）+ DuckDuckGo（降级）双引擎搜索
- web_fetch: 抓取指定 URL 网页正文
- date_planning_search: 专为约会策划设计的本地化联网搜索
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger

from cyber_wingman.agent.tools.base import Tool


def _tavily_api_key() -> str | None:
    return os.getenv("TAVILY_API_KEY")


async def _tavily_search(query: str, max_results: int = 6) -> list[dict[str, Any]] | None:
    """调用 Tavily Search API（为 Agent 优化的搜索引擎）。"""
    api_key = _tavily_api_key()
    if not api_key:
        return None
    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=api_key)
        resp = await client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
        )
        results = resp.get("results", [])
        answer = resp.get("answer", "")
        return [{"answer": answer, "results": results}]
    except Exception as e:
        logger.warning("event=tavily_search_failed query={} error={}", query, str(e))
        return None


async def _ddg_search(query: str, max_results: int = 5) -> list[dict[str, Any]] | None:
    """DuckDuckGo 降级搜索。"""
    try:
        import asyncio

        from duckduckgo_search import DDGS

        def _run():
            return list(DDGS().text(query, max_results=max_results) or [])

        return await asyncio.to_thread(_run)
    except Exception as e:
        logger.warning("event=ddg_search_failed query={} error={}", query, str(e))
        return None


def _format_tavily(data: list[dict[str, Any]], query: str) -> str:
    item = data[0]
    answer = item.get("answer", "")
    results: list[dict[str, Any]] = item.get("results", [])
    lines = [f"[Tavily 搜索] 查询: {query}"]
    if answer:
        lines.append(f"\n💡 AI 摘要: {answer}")
    lines.append("")
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "")[:300]
        lines.append(f"{i}. {title}\nURL: {url}\n{content}")
    return "\n".join(lines)


def _format_ddg(results: list[dict[str, Any]], query: str) -> str:
    lines = [f"[DuckDuckGo 搜索] 查询: {query}\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        href = r.get("href", "")
        body = r.get("body", "")[:300]
        lines.append(f"{i}. {title}\nURL: {href}\n{body}")
    return "\n\n".join(lines)


class WebSearchTool(Tool):
    """全网搜索 — Tavily 主引擎 + DuckDuckGo 降级。"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "全网并发搜索工具。**极其重要**：凡是涉及现实世界物理地点（如约会选址、餐厅、商场）、"
            "当前事件、天气、价格、最新资讯或具体客观事实的任务，必须绝对优先使用 `web_search` 获取真实数据，"
            "严禁仅凭模型内部记忆捏造或猜测。\n"
            "**使用规范**：严禁串行试探搜索。你必须提前思考所有需要排查的情报（如同时查天气、餐厅、活动），"
            "将其组合为一个 `queries` 数组一次性提交，底层将并发搜索以节省时间。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "并发搜索关键词数组（最多并发3-5个，尽量简洁精确）",
                },
            },
            "required": ["queries"],
        }

    async def execute(self, **kwargs: Any) -> str:
        import asyncio
        queries = kwargs.get("queries", [])
        if not queries or not isinstance(queries, list):
            return "Error: queries 必须是非空字符串数组"

        results_text = []

        async def _search_single(q: str) -> str:
            q = q.strip()
            if not q:
                return ""
            # 主引擎: Tavily
            tavily_data = await _tavily_search(q)
            if tavily_data:
                logger.info("event=web_search_tavily query={}", q)
                return _format_tavily(tavily_data, q)

            # 降级: DuckDuckGo
            logger.info("event=web_search_fallback_ddg query={}", q)
            ddg_data = await _ddg_search(q)
            if ddg_data:
                return _format_ddg(ddg_data, q)

            return f"[Web 搜索] 查询: {q}\n未找到相关结果。"

        # Concurrent execution
        tasks = [_search_single(q) for q in queries]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, res in enumerate(gathered):
            if isinstance(res, Exception):
                logger.error("event=web_search_error query={} error={}", queries[idx], str(res))
                results_text.append(f"[Web 搜索] 查询: {queries[idx]}\n发生错误: {str(res)}")
            elif res:
                results_text.append(res)

        return "\n\n" + "-" * 40 + "\n\n".join(results_text) if results_text else "Error: 所有查询均无结果"


class DatePlanningSearchTool(Tool):
    """
    约会策划搜索 — 专为约会场景优化的联网搜索工具。

    搜索餐厅、活动、景点等，并结合城市和预算条件给出结构化行程建议。
    """

    @property
    def name(self) -> str:
        return "date_planning_search"

    @property
    def description(self) -> str:
        return (
            "为用户约会策划并发联网搜索场地/餐厅/活动。"
            "当用户提到约会策划、带她去哪、情侣活动等关键词时调用。\n"
            "**使用规范**：严禁串行试探！你必须一次性想好所有要排查的类型（如：看展、高端餐厅、饭后散步点），"
            "将其组合为一个 `themes` 数组一次性提交，底层将并发搜索返回综合推荐。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称（如：上海、北京、成都）",
                },
                "themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "约会主题或类型数组（如：['高端浪漫餐厅', '艺术展览', '密室逃脱']）",
                },
                "budget": {
                    "type": "string",
                    "description": "预算范围（如：人均100元以内、人均200-500元、不限）",
                },
            },
            "required": ["city", "themes"],
        }

    async def execute(self, **kwargs: Any) -> str:
        import asyncio
        city = kwargs.get("city", "").strip()
        themes = kwargs.get("themes", [])
        budget = kwargs.get("budget", "不限")

        if not city or not themes or not isinstance(themes, list):
            return "Error: 城市和约会主题数组(themes)不能为空"

        results_text = []

        async def _search_theme(theme: str) -> str:
            theme = theme.strip()
            if not theme:
                return ""
            # 构建专门的约会搜索词
            query = f"{city} {theme} 约会 推荐 {budget} 2024"
            logger.info("event=date_planning_search city={} theme={} budget={}", city, theme, budget)

            # 主引擎: Tavily
            tavily_data = await _tavily_search(query, max_results=5)
            if tavily_data:
                item = tavily_data[0]
                answer = item.get("answer", "")
                results: list[dict[str, Any]] = item.get("results", [])

                lines = [f"🗺️ [{city}·{theme}] 约会场地结果 (预算: {budget})"]
                if answer:
                    lines.append(f"💡 综合推荐: {answer}")
                for i, r in enumerate(results[:4], 1):
                    title = r.get("title", "")
                    content = r.get("content", "")[:300]
                    lines.append(f"{i}. **{title}**\n   {content}")
                return "\n".join(lines)

            # 降级: DuckDuckGo
            ddg_data = await _ddg_search(query, max_results=4)
            if ddg_data:
                lines = [f"🗺️ [{city}·{theme}] 约会场地推荐:\n"]
                for i, r in enumerate(ddg_data, 1):
                    lines.append(f"{i}. {r.get('title', '')}\n   {r.get('body', '')[:200]}")
                return "\n".join(lines)

            return f"🗺️ [{city}·{theme}] 未找到合适场地推荐。"

        tasks = [_search_theme(th) for th in themes]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, res in enumerate(gathered):
            if isinstance(res, Exception):
                logger.error("event=date_planning_search_error theme={} error={}", themes[idx], str(res))
                results_text.append(f"[约会策划] 主题: {themes[idx]} 发生错误: {str(res)}")
            elif res:
                results_text.append(res)

        final_result = "\n\n" + "-" * 40 + "\n\n".join(results_text) if results_text else "Error: 所有主题均无结果"
        
        final_result += (
            "\n\n---\n以上是初步的场地并发搜索结果。"
            "请自行判断是否需要组合使用其他工具（如查天气、时间等）补充环境信息。"
            "必须在所有环境信息收集完毕后，再向用户输出最终的约会行程单。"
        )
        return final_result


class WebFetchTool(Tool):
    """抓取网页内容。"""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "抓取指定 URL 的网页内容，提取正文文本。"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要抓取的网页 URL",
                },
            },
            "required": ["url"],
        }

    async def execute(self, **kwargs: Any) -> str:
        url = kwargs.get("url", "")
        if not url:
            return "Error: URL 不能为空"

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "CyberWingman/0.1"})
                resp.raise_for_status()
                text = resp.text[:10000]
                return f"[网页内容] URL: {url}\n\n{text}"
        except httpx.TimeoutException:
            logger.warning("event=web_fetch_timeout url={}", url)
            return f"Error: 抓取超时 (30s): {url}"
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP {e.response.status_code}: {url}"
        except Exception as e:
            logger.error("event=web_fetch_failed url={url} error={error}", url=url, error=str(e))
            return f"Error: 抓取失败: {e}"

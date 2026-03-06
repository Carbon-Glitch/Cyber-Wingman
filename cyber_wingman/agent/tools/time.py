import datetime
from typing import Any

from cyber_wingman.agent.tools.base import Tool


class TimeAwarenessTool(Tool):
    """时间感知与日历工具 — 获取当前精确时间与日期计算。"""

    @property
    def name(self) -> str:
        return "time_awareness"

    @property
    def description(self) -> str:
        return (
            "获取当前的实时时间、日期、星期几。当你需要帮用户做时间规划、日程安排、或者判断该不该"
            "发消息时，请先调用此工具获取最新的系统时间作为基准。"
            "如果不提供 offset_days，默认返回当前系统时间。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "offset_days": {
                    "type": "integer",
                    "description": "天数偏移量（负数表示过去，正数表示未来，0或不传表示现在）",
                },
                "timezone_name": {
                    "type": "string",
                    "description": "时区名称（如 Asia/Shanghai，默认系统本地时区）",
                },
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        import zoneinfo

        offset = kwargs.get("offset_days", 0)
        tz_name = kwargs.get("timezone_name", "")

        try:
            tz = zoneinfo.ZoneInfo(tz_name) if tz_name else None
            now = datetime.datetime.now(tz=tz)
            if offset:
                target_date = now + datetime.timedelta(days=offset)
                time_str = target_date.strftime("%Y-%m-%d %H:%M:%S")
                weekday = target_date.strftime("%A")
                return f"目标时间 (偏移了 {offset} 天): {time_str}，星期: {weekday}"
            else:
                time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                weekday = now.strftime("%A")
                return f"当前系统时间: {time_str}，星期: {weekday}"
        except Exception as e:
            return f"Error: 无法获取时间 - {str(e)}"

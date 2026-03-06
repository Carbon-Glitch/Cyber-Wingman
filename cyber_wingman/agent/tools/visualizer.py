import json
from typing import Any

from loguru import logger

from cyber_wingman.agent.tools.base import Tool


class DataVisualizerTool(Tool):
    """关系雷达数据可视化工具。"""

    @property
    def name(self) -> str:
        return "data_visualizer"

    @property
    def description(self) -> str:
        return (
            "为前端生成结构化的雷达图数据或关系健康图表数据。包含：吸引力、亲密度、顺从度/服从性、情绪价值、防御心理、投资度 等 6 个维度的评分。"
            "当你需要向用户直观展示TA与目标的‘当前关系雷达状态’时，请调用此工具生成 Canvas 渲染所需的数据。"
            "数据必须为 0-100 的整数或浮点数。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "attraction": {"type": "number", "description": "吸引力 (0-100)"},
                "intimacy": {"type": "number", "description": "亲密度 (0-100)"},
                "compliance": {"type": "number", "description": "服从性/顺从度 (0-100)"},
                "emotional_value": {"type": "number", "description": "情绪价值提供 (0-100)"},
                "defensiveness": {"type": "number", "description": "防御心理/反感度 (0-100, 数值越低代表关系越深/越好)"},
                "investment": {"type": "number", "description": "时间与精力投资度 (0-100)"},
                "analysis": {"type": "string", "description": "一句简短的情感状态总结/判词"},
            },
            "required": ["attraction", "intimacy", "compliance", "emotional_value", "defensiveness", "investment"],
        }

    async def execute(self, **kwargs: Any) -> str:
        context = kwargs.pop("_context", {})
        on_progress = context.get("_on_progress")

        try:
            # Generate the chart data JSON representation
            chart_data = {
                "radar": {
                    "attraction": kwargs.get("attraction", 0),
                    "intimacy": kwargs.get("intimacy", 0),
                    "compliance": kwargs.get("compliance", 0),
                    "emotional_value": kwargs.get("emotional_value", 0),
                    "defensiveness": kwargs.get("defensiveness", 0),
                    "investment": kwargs.get("investment", 0),
                },
                "summary": kwargs.get("analysis", "数据分析完成。")
            }
            json_str = json.dumps(chart_data, ensure_ascii=False, indent=2)

            # Fire SSE event to frontend if streaming is available
            if on_progress:
                logger.info("event=chart_data_generated summary={}", chart_data["summary"])
                await on_progress(
                    chart_data["summary"],
                    event_type="render_chart",
                    chart_data=chart_data,
                )

            return f"成功生成并在前端展示了关系雷达图表，分析总结：{chart_data['summary']}\n图表数据：\n{json_str}"

        except Exception as e:
            return f"Error: 生成图表数据失败 - {str(e)}"

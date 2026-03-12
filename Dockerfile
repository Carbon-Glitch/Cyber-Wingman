# ─── Stage 1: 依賴安裝 ───────────────────────────────────────────
FROM python:3.12-slim AS builder

# 安裝 uv（官方方式，不依賴 mise）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 優先複製依賴清單，利用 Docker cache 層
COPY pyproject.toml uv.lock ./

# 安裝正式依賴（不含 dev，且在複製程式碼前不預先安裝專案本身）
RUN uv sync --frozen --no-dev --no-install-project

# ─── Stage 2: 執行鏡像 ───────────────────────────────────────────
FROM python:3.12-slim AS runtime

# 複製 uv 工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 從 builder 複製已安裝的虛擬環境
COPY --from=builder /app/.venv /app/.venv

# 複製應用程式碼（排除不需要的目錄，由 .dockerignore 控制）
COPY cyber_wingman/ ./cyber_wingman/
COPY prompt/ ./prompt/

# 確保 venv 的 bin 優先於系統 PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Railway 會注入 $PORT 環境變數；fallback 為 8000
CMD ["sh", "-c", "uvicorn cyber_wingman.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]

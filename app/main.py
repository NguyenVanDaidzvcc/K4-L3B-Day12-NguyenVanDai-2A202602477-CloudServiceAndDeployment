"""Agent service — điểm ráp nối của cả lab: CP1, CP3, CP4.

Luồng xử lý một request /ask:
    1. Xác thực API key.
    2. Kiểm tra rate limit.
    3. Kiểm tra ngân sách.
    4. Đọc lịch sử từ store.
    5. Gọi mock LLM.
    6. Lưu câu hỏi và câu trả lời.
    7. Ghi nhận chi phí.
    8. Ghi log và trả response.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from utils.mock_llm import ask_llm

from .auth import verify_api_key
from .config import get_settings
from .cost_guard import CostGuard
from .lifecycle import lifecycle
from .logging_utils import log_event
from .rate_limiter import RateLimiter
from .store import ConversationStore, get_redis_client

SERVICE_NAME = "day12-agent"
SERVICE_VERSION = "1.0.0"


# Providers:
# Tách dependency thành hàm để bộ test có thể thay bằng Redis giả
# thông qua app.dependency_overrides.
# Cache object để không tạo lại provider ở mỗi request.


@lru_cache(maxsize=1)
def get_store() -> ConversationStore:
    return ConversationStore(get_redis_client())


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    return RateLimiter(
        get_redis_client(),
        get_settings().rate_limit_per_minute,
    )


@lru_cache(maxsize=1)
def get_cost_guard() -> CostGuard:
    return CostGuard(
        get_redis_client(),
        get_settings().monthly_budget_usd,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Chạy khi ứng dụng khởi động và khi tắt.

    get_settings() được gọi trước yield để thiếu API key
    sẽ làm startup thất bại ngay, không chờ request đầu tiên.
    """

    get_settings()

    lifecycle.shutting_down = False
    lifecycle.install()

    log_event(
        "service_started",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )

    try:
        yield
    finally:
        lifecycle.shutting_down = True
        lifecycle.restore()

        log_event(
            "service_stopped",
            service=SERVICE_NAME,
        )


app = FastAPI(
    title="Day 12 Production Agent",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    """Dữ liệu đầu vào cho endpoint /ask.

    Câu hỏi phải có ít nhất 1 ký tự, tối đa 2000 ký tự.
    """

    question: str = Field(min_length=1, max_length=2000)


# Health và readiness.


@app.get("/health")
def health():
    """Liveness probe — process còn sống không?

    TODO (CP1 + CP4):
      - Bình thường: trả 200 với status, service, version.
      - Đang shutdown: trả 503 với status shutting_down.

    Endpoint này phải nhẹ và không gọi Redis hoặc database.
    Nếu liveness phụ thuộc Redis, sự cố Redis có thể khiến
    orchestrator restart những process vẫn đang hoạt động.
    """

    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@app.get("/ready")
def ready(store: ConversationStore = Depends(get_store)):
    """Readiness probe — đã sẵn sàng nhận traffic chưa?

    TODO (CP4):
      - Đang shutdown: trả 503.
      - Redis không phản hồi: trả 503.
      - Redis hoạt động: trả 200.

    Khác /health, endpoint này kiểm tra dependency.
    Hệ thống định tuyến có thể dùng readiness để quyết định
    có gửi traffic vào instance hay không.
    """

    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )

    if not store.ping():
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "redis": False,
            },
        )

    return {
        "status": "ready",
        "redis": True,
    }


# Endpoint chính.


@app.post("/ask")
def ask(
    payload: AskRequest,
    user_id: str = Depends(verify_api_key),
    store: ConversationStore = Depends(get_store),
    limiter: RateLimiter = Depends(get_rate_limiter),
    guard: CostGuard = Depends(get_cost_guard),
):
    """Hỏi agent một câu.

    TODO (CP3 + CP4) — thực hiện đúng thứ tự:
      1. limiter.check(user_id): 429 nếu vượt hạn mức.
      2. guard.check(user_id): 402 nếu vượt ngân sách.
      3. store.get_history(user_id).
      4. ask_llm(payload.question, history).
      5. Lưu message user và assistant.
      6. guard.record() để cộng chi phí.
      7. log_event() ghi token và chi phí.
      8. Trả answer, user_id, history_length, cost_usd, tokens.

    Kiểm tra trước khi gọi LLM vì chi phí phát sinh
    ở bước gọi model. Chặn sau khi gọi không tránh được phí.

    Dependency verify_api_key sẽ trả 401 nếu khóa không hợp lệ,
    trước khi chạy phần thân endpoint này.
    """

    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )

    # Kiểm tra hạn mức trước khi gọi LLM.
    limiter.check(user_id)
    guard.check(user_id)

    # Đọc lịch sử trước khi thêm lượt hỏi mới.
    history = store.get_history(user_id)

    # Bài lab dùng mock LLM, không cần OpenAI API key.
    result = ask_llm(payload.question, history)

    # Lưu cả câu hỏi và câu trả lời.
    store.append(user_id, "user", payload.question)
    store.append(user_id, "assistant", result["answer"])

    # Ghi nhận chi phí sau khi có kết quả.
    guard.record(user_id, result["cost_usd"])

    log_event(
        "ask_completed",
        user_id=user_id,
        tokens_in=result["tokens_in"],
        tokens_out=result["tokens_out"],
        cost_usd=result["cost_usd"],
    )

    return {
        "answer": result["answer"],
        "user_id": user_id,
        # Độ dài history trước lượt hỏi; mỗi lượt hoàn tất thêm 2 message.
        "history_length": len(history),
        "cost_usd": result["cost_usd"],
        "tokens": {
            "in": result["tokens_in"],
            "out": result["tokens_out"],
        },
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
    )

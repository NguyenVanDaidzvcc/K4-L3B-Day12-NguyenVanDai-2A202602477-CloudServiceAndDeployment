"""CP3 — Xác thực bằng API key.

Endpoint công khai cần kiểm tra quyền truy cập trước khi
cho phép gọi LLM hoặc sử dụng tài nguyên của service.
"""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException

from .config import get_settings

ANONYMOUS_USER = "anonymous"


def verify_api_key(
    x_api_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    """Kiểm tra header X-API-Key; trả về user_id nếu hợp lệ.

    TODO (CP3):
      1. Lấy khóa đúng từ get_settings().agent_api_key.
      2. Thiếu khóa hoặc sai khóa: trả HTTP 401.
      3. So sánh bằng secrets.compare_digest.
      4. Hợp lệ: trả x_user_id nếu có, ngược lại anonymous.

    compare_digest được thiết kế để giảm rò rỉ thông tin
    thời gian khi so sánh secret.

    Trong bài lab, X-User-Id do client cung cấp và được dùng
    làm đơn vị tính rate limit, lịch sử và chi phí.
    Đây chưa phải cơ chế xác minh danh tính người dùng.
    """

    expected = get_settings().agent_api_key

    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(),
        expected.encode(),
    ):
        raise HTTPException(
            status_code=401,
            detail="invalid or missing API key",
        )

    return x_user_id or ANONYMOUS_USER
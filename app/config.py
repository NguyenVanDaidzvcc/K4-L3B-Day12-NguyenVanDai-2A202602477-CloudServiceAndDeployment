"""CP1 — Cấu hình theo 12-Factor.

Cấu hình được đọc từ biến môi trường để cùng một image có thể chạy
ở laptop, staging và production mà không phải sửa code.
Các cấu hình không phải secret có thể có giá trị mặc định.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toàn bộ cấu hình của service.

    TODO (CP1): khai báo các trường dưới đây.

    pydantic-settings tự đọc biến môi trường theo tên trường,
    không phân biệt hoa thường. Ví dụ:
        agent_api_key đọc từ AGENT_API_KEY.

    | Trường                | Kiểu  | Mặc định                  |
    |-----------------------|-------|---------------------------|
    | port                  | int   | 8000                      |
    | agent_api_key         | str   | Bắt buộc, không mặc định  |
    | redis_url             | str   | redis://localhost:6379/0  |
    | rate_limit_per_minute | int   | 10                        |
    | monthly_budget_usd    | float | 10.0                      |
    | log_level             | str   | INFO                      |

    Vì sao agent_api_key không có mặc định?
    Nếu quên cấu hình secret trên cloud, ứng dụng phải báo lỗi ngay
    khi khởi động thay vì chạy với một khóa mặc định không an toàn.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Cổng hợp lệ nằm trong khoảng 1–65535.
    port: int = Field(default=8000, ge=1, le=65535)

    # Không có default: bắt buộc phải cấu hình.
    # min_length=1 cũng chặn trường hợp khóa là chuỗi rỗng.
    agent_api_key: str = Field(min_length=1)

    redis_url: str = "redis://localhost:6379/0"

    # Hạn mức request phải lớn hơn 0.
    rate_limit_per_minute: int = Field(default=10, gt=0)

    # Ngân sách không âm và không nhận NaN/Infinity.
    monthly_budget_usd: float = Field(
        default=10.0,
        ge=0,
        allow_inf_nan=False,
    )

    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Đọc cấu hình một lần rồi cache lại.

    Không cần đọc lại biến môi trường ở mỗi request.
    """
    return Settings()
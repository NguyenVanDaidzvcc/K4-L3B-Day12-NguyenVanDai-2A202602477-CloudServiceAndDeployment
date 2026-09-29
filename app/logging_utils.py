"""CP1 — Structured logging.

Log JSON giúp hệ thống thu thập log lọc, thống kê và cảnh báo
theo các trường dữ liệu như event, user_id, cost_usd.

Mỗi sự kiện phải nằm trên một dòng để không bị tách thành
nhiều bản ghi khi hệ thống đọc stdout.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """CHO SẴN — thời điểm hiện tại theo ISO-8601, múi giờ UTC."""
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, level: str = "info", **fields) -> str:
    """Ghi một dòng log JSON ra stdout.

    TODO (CP1):
      1. Tạo dict gồm tối thiểu:
         - event: tên sự kiện.
         - level: mức log viết thường.
         - timestamp: thời điểm UTC.
      2. Gộp các trường bổ sung từ **fields.
      3. Chuyển thành JSON trên một dòng.
      4. In ra stdout và trả về chính chuỗi JSON đó.

    ensure_ascii=False giữ nguyên nội dung tiếng Việt.
    Không dùng indent vì sẽ làm một sự kiện xuống nhiều dòng.

    Ví dụ:
        log_event(
            "ask_completed",
            user_id="sv01",
            cost_usd=0.0001,
        )
    """

    # Đặt các trường chuẩn sau fields để timestamp chuẩn
    # không bị ghi đè bởi dữ liệu bổ sung.
    record = {
        **fields,
        "event": event,
        "level": level.lower(),
        "timestamp": utc_now_iso(),
    }

    line = json.dumps(record, ensure_ascii=False)

    # flush=True giúp log xuất hiện ngay trên terminal/cloud.
    print(line, flush=True)

    return line
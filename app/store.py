"""CP4 — Stateless: state sống ngoài process.

Nếu lưu lịch sử hội thoại trong dict Python, mỗi instance
sẽ có một bản dữ liệu riêng.

Khi request đầu vào instance A nhưng request tiếp theo vào
instance B, người dùng có thể bị mất lịch sử.

Redis là nơi lưu dữ liệu dùng chung giữa các instance.
"""

from __future__ import annotations

import json

import redis

from .config import get_settings

HISTORY_MAX_MESSAGES = 20
HISTORY_TTL_SECONDS = 7 * 24 * 3600


def get_redis_client(url: str | None = None):
    """Tạo client Redis từ URL.

    fake:// trả về Redis giả chạy trong RAM, phục vụ học
    và chạy thử khi chưa có Redis thật.

    Không dùng fake:// để triển khai nhiều instance:
    dữ liệu vẫn nằm trong process và không được chia sẻ.
    """

    url = url or get_settings().redis_url

    if url.startswith("fake://"):
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)

    # Timeout giúp readiness không chờ vô hạn khi Redis lỗi.
    return redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


class ConversationStore:
    """Lưu lịch sử hội thoại của từng user trong Redis List."""

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _key(user_id: str) -> str:
        """CHO SẴN — key lịch sử riêng cho từng user."""
        return f"history:{user_id}"

    def ping(self) -> bool:
        """Redis có phản hồi không? Dùng cho /ready.

        TODO (CP4):
          1. Gọi client.ping() trong try/except.
          2. Thành công: trả True.
          3. Mất kết nối hoặc lỗi khác: trả False.

        Không để exception kết nối Redis thoát khỏi hàm.
        """

        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def append(
        self,
        user_id: str,
        role: str,
        content: str,
    ) -> None:
        """Ghi thêm một message vào lịch sử.

        TODO (CP4):
          1. Chuyển message thành JSON và RPUSH vào list.
          2. LTRIM để chỉ giữ các message mới nhất.
          3. EXPIRE để hội thoại cũ tự hết hạn.

        Giới hạn lịch sử giúp tránh prompt tăng vô hạn.
        """

        key = self._key(user_id)

        message = json.dumps(
            {"role": role, "content": content},
            ensure_ascii=False,
        )

        with self.client.pipeline(transaction=True) as pipe:
            pipe.rpush(key, message)
            pipe.ltrim(key, -HISTORY_MAX_MESSAGES, -1)
            pipe.expire(key, HISTORY_TTL_SECONDS)
            pipe.execute()

    def get_history(self, user_id: str) -> list[dict]:
        """Đọc lịch sử theo thứ tự cũ nhất trước.

        TODO (CP4):
          1. LRANGE từ 0 đến -1 để đọc toàn bộ list.
          2. json.loads từng message.
          3. Chưa có lịch sử: trả list rỗng.
        """

        items = self.client.lrange(self._key(user_id), 0, -1)
        return [json.loads(item) for item in items]

    def clear(self, user_id: str) -> None:
        """CHO SẴN — xóa lịch sử của một user."""
        self.client.delete(self._key(user_id))
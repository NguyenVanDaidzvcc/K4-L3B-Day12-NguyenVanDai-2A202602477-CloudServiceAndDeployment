"""CP3 — Rate limiting bằng thuật toán sliding window.

Đếm số request trong 60 giây gần nhất, thay vì đếm theo
phút đồng hồ.

Nếu reset bộ đếm ở đầu mỗi phút, người dùng có thể gửi
10 request ở cuối phút trước và 10 request ở đầu phút sau.

Cấu trúc dữ liệu:
    Redis Sorted Set.
    Score = timestamp của request.
    Member = timestamp kết hợp UUID để tránh trùng.

Bản triển khai dùng WATCH/MULTI để bảo vệ quota khi nhiều
instance cùng xử lý request cho một user.
"""

from __future__ import annotations

import time
import uuid

from fastapi import HTTPException
from redis.exceptions import WatchError

WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self, client, limit_per_minute: int) -> None:
        self.client = client
        self.limit = limit_per_minute

    @staticmethod
    def _key(user_id: str) -> str:
        """CHO SẴN — mỗi user có một key riêng."""
        return f"ratelimit:{user_id}"

    def hit_count(
        self,
        user_id: str,
        now: float | None = None,
    ) -> int:
        """Số request trong WINDOW_SECONDS giây gần nhất.

        TODO (CP3):
          1. Lấy thời gian hiện tại nếu chưa truyền now.
          2. Xóa entry đã ra khỏi cửa sổ.
          3. Trả về số entry còn lại.

        Pipeline transaction gom thao tác xóa và đếm
        vào cùng một giao dịch Redis.
        """

        now = time.time() if now is None else now
        key = self._key(user_id)

        with self.client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(
                key,
                "-inf",
                now - WINDOW_SECONDS,
            )
            pipe.zcard(key)

            results = pipe.execute()
            return int(results[1])

    def check(
        self,
        user_id: str,
        now: float | None = None,
    ) -> None:
        """Cho qua nếu còn quota, ngược lại trả HTTP 429.

        TODO (CP3):
          1. Đếm request trong cửa sổ 60 giây.
          2. Nếu số request >= limit: trả 429.
          3. Nếu còn quota: ghi nhận request mới.
          4. Đặt TTL để key tự dọn.

        Phải kiểm tra trước rồi mới ghi nhận để request
        thứ limit vẫn được chấp nhận.

        Không gọi hit_count riêng ở đây vì cần bảo vệ
        cả bước kiểm tra và ghi nhận bằng WATCH/MULTI.
        Nếu key bị instance khác sửa, thử lại giao dịch.
        """

        now = time.time() if now is None else now
        key = self._key(user_id)

        while True:
            with self.client.pipeline() as pipe:
                try:
                    # Theo dõi thay đổi của key trước khi đọc.
                    pipe.watch(key)

                    # Dấu "(" nghĩa là không bao gồm biên dưới.
                    count = pipe.zcount(
                        key,
                        f"({now - WINDOW_SECONDS}",
                        "+inf",
                    )

                    if count >= self.limit:
                        raise HTTPException(
                            status_code=429,
                            detail="rate limit exceeded",
                            headers={
                                "Retry-After": str(WINDOW_SECONDS)
                            },
                        )

                    # Bắt đầu nhóm lệnh ghi nguyên tử.
                    pipe.multi()

                    pipe.zremrangebyscore(
                        key,
                        "-inf",
                        now - WINDOW_SECONDS,
                    )

                    # UUID đảm bảo hai request cùng timestamp
                    # không ghi đè lên nhau.
                    pipe.zadd(
                        key,
                        {f"{now}:{uuid.uuid4().hex}": now},
                    )

                    pipe.expire(key, WINDOW_SECONDS)
                    pipe.execute()

                    return

                except WatchError:
                    # Key thay đổi sau WATCH: đọc lại quota.
                    continue
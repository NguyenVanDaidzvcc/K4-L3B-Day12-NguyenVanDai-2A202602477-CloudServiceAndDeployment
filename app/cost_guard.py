"""CP3 — Cost guard: kiểm soát chi phí theo tháng.

Rate limit giới hạn số request.
Cost guard giới hạn chi phí đã ghi nhận theo user/tháng.

Một user có thể gọi ít request nhưng mỗi request sử dụng
nhiều token, nên vẫn cần theo dõi ngân sách riêng.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

# Giữ dữ liệu chi tiêu thêm khoảng 40 ngày.
KEY_TTL_SECONDS = 40 * 24 * 3600


class CostGuard:
    def __init__(self, client, monthly_budget_usd: float) -> None:
        self.client = client
        self.budget = monthly_budget_usd

    @staticmethod
    def current_month() -> str:
        """CHO SẴN — nhãn tháng hiện tại dạng YYYY-MM, theo UTC."""
        return datetime.now(timezone.utc).strftime("%Y-%m")

    @classmethod
    def _key(
        cls,
        user_id: str,
        month: str | None = None,
    ) -> str:
        """CHO SẴN — khóa Redis theo từng user và từng tháng."""
        return f"cost:{user_id}:{month or cls.current_month()}"

    def spent(
        self,
        user_id: str,
        month: str | None = None,
    ) -> float:
        """Số tiền user đã tiêu trong tháng.

        TODO (CP3):
          1. Đọc giá trị từ Redis.
          2. Key chưa tồn tại: trả 0.0.
          3. Ép kiểu float vì Redis có thể trả chuỗi.
        """

        value = self.client.get(self._key(user_id, month))
        return float(value or 0.0)

    def check(
        self,
        user_id: str,
        estimated_cost: float = 0.0,
        month: str | None = None,
    ) -> None:
        """Cho qua nếu còn ngân sách, ngược lại trả HTTP 402.

        TODO (CP3):
            spent + estimated_cost > budget
            -> HTTPException 402.

        402 là Payment Required.

        Theo luồng bài lab, /ask kiểm tra trước rồi ghi nhận
        chi phí sau khi gọi LLM. Cơ chế này chưa giữ chỗ
        ngân sách nguyên tử cho các request đồng thời.
        """

        if self.spent(user_id, month) + estimated_cost > self.budget:
            raise HTTPException(
                status_code=402,
                detail="monthly budget exceeded",
            )

    def record(
        self,
        user_id: str,
        cost: float,
        month: str | None = None,
    ) -> float:
        """Cộng dồn chi phí và trả tổng mới.

        TODO (CP3):
          1. Cộng cost bằng INCRBYFLOAT.
          2. Đặt thời hạn cho key.
          3. Trả tổng chi phí mới.

        Pipeline đảm bảo thao tác cộng và đặt TTL
        được thực hiện trong cùng giao dịch.
        """

        key = self._key(user_id, month)

        with self.client.pipeline(transaction=True) as pipe:
            pipe.incrbyfloat(key, cost)
            pipe.expire(key, KEY_TTL_SECONDS)

            results = pipe.execute()
            return float(results[0])
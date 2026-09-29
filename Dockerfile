# CP2 — Containerization
#
# Yêu cầu của bài:
#   - Multi-stage build: builder cài dependency.
#   - Runtime dùng base image slim.
#   - COPY requirements.txt và pip install trước khi COPY source.
#   - Chạy bằng user thường.
#   - HEALTHCHECK gọi /health.
#   - Đọc cổng từ biến môi trường PORT.
#
# Kiểm tra:
#   pytest tests/test_cp2.py -v
#
# Build:
#   docker build -t day12-agent:prod .
#
# Xem dung lượng:
#   docker images day12-agent:prod
#
# Chạy non-root giảm quyền của process trong container.
# Root trong container không tự động đồng nghĩa root trên host.


# Stage 1: cài dependency vào virtual environment.
FROM python:3.11-slim AS builder

WORKDIR /build

# Tách requirements thành layer riêng để tận dụng cache.
COPY requirements.txt .

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: môi trường chạy ứng dụng.
FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Tạo user thường để chạy service.
RUN groupadd --system app && useradd --system --gid app --uid 10001 app

# Copy dependency đã cài từ builder.
COPY --from=builder /opt/venv /opt/venv

# Chỉ copy source cần chạy, không copy toàn bộ repo.
COPY --chown=app:app app ./app
COPY --chown=app:app utils ./utils

USER app

# EXPOSE là thông tin mô tả cổng mặc định.
# Cổng thực tế của server được đọc từ PORT khi chạy.
EXPOSE 8000

# Kiểm tra liveness bằng thư viện chuẩn Python.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health',timeout=3)"

# exec giúp Uvicorn nhận trực tiếp tín hiệu dừng.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 25"]
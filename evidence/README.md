# Kết quả kiểm tra thực tế — 2026-10-02

- Python trong `.venv`: 80 test offline pass (CP1–CP4 và bonus tĩnh).
- Image `day12-agent:prod`: Docker báo 218 MB, nhỏ hơn 500 MB.
- Image đối chiếu `day12-agent:single`: Docker báo 1.19 GB.
- Process container: `uid=10001(app) gid=999(app) groups=999(app)`.
- Compose đã chạy ba agent healthy, Redis healthy và Nginx ở cổng 8000.
- `local-smoke.json`: kết quả API thật; `/health` và `/ready` 200,
  thiếu key 401, 10 request 200 rồi 5 request 429, lịch sử `0,2,...,18`.
- `agent-smoke.txt`: log thật từ nhiều agent cho cùng user trong lần kiểm tra.
- `local-smoke-after-move.json`: kiểm tra lại API thành công sau khi chuyển Docker.
- `../screenshots/health-local.png`: ảnh chụp trực tiếp endpoint local bằng Edge.
- `grade.txt`: CP1 13/13, CP2 16/16, CP3 22/22, CP4 19/19;
  CP5 0/8 (5 skip), exercises 9/10, bonus 12/13. Tổng tự động 92.7/100,
  chưa trừ lỗi tên repo và chưa đánh giá thủ công phần phản ánh.

## Khắc phục môi trường và giới hạn

Sau các phép đo trên, ổ C hết dung lượng khi kiểm tra cache build.
Docker engine sau đó ngừng phản hồi. Đã chuyển dữ liệu WSL Docker từ D sang E
và log Docker từ C sang E, kiểm tra hash 1533 file log trước khi chuyển đường
dẫn. Docker khởi động lại thành công và stack ba agent đã chạy lại healthy.

`build-cache.txt` xác nhận sau khi sửa comment trong `app/main.py`, các layer
cài dependency dùng cache, các layer copy source chạy lại.
`image-sizes.txt` chứa dung lượng image tính theo byte.

Chưa có minh chứng deploy cloud, screenshot dashboard hoặc workflow GitHub xanh.
Ảnh local và output không thay thế minh chứng cloud được yêu cầu.

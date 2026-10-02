# Đặt ảnh chụp màn hình bản deploy vào thư mục này

- `dashboard.png`: chụp dashboard Railway/Render của service đang chạy.
- `health.png`: chụp trình duyệt/curl gọi Public URL `/health` trả 200.
- Nếu chọn local fallback, chụp `docker compose ps` và kết quả API local;
  ghi rõ đây là Docker cục bộ trong `DEPLOYMENT.md` (CP5 tối đa 9/15).

Che secret nếu dashboard có hiển thị. Dùng ảnh chụp thật sau khi service chạy;
không dùng ảnh dựng hoặc ảnh của lần deploy khác.

Đã có `health-local.png`: ảnh Edge headless chụp trực tiếp
`http://localhost:8000/health` ngày 2026-10-02 sau khi chuyển Docker sang E.
Đây là minh chứng local, không phải ảnh deploy cloud.

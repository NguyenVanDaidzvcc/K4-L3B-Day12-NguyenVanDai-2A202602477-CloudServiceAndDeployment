# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Nguyễn Văn Đại |
| Mã học viên | 2A202602477 |
| Repo | https://github.com/NguyenVanDaidzvcc/K4-L3B-Day12-NguyenVanDai-2A202602477-CloudServiceAndDeployment |

Tên repo hiện tại cần đổi thành
`K4-L3B-DAY12-NguyenVanDai-2A202602477-CloudServicesAndDeployment` trước khi nộp;
cập nhật link ở đây và badge README sau khi đổi tên trên GitHub.

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://TODO-thay-bang-url-that.up.railway.app |
| Platform | Railway / Render / Cloud Run — (điền platform bạn dùng) |
| Ngày deploy | (điền ngày) |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | Chưa xác minh | platform tự gán |
| `AGENT_API_KEY` | Chưa xác minh | đặt trong dashboard, không nằm trong repo |
| `REDIS_URL` | Chưa xác minh | (điền: Redis add-on của platform / Upstash / ...) |
| `RATE_LIMIT_PER_MINUTE` | Chưa xác minh | dự kiến 10 |
| `MONTHLY_BUDGET_USD` | Chưa xác minh | dự kiến 10.0 |
| `LOG_LEVEL` | Chưa xác minh | dự kiến INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

### Đã kiểm tra tại máy (chưa phải cloud)

Stack Nginx + 3 agent + Redis đã chạy và kiểm tra ngày 2026-10-02:

- `http://localhost:8000/health`: 200, `status=ok`.
- `/ready`: 200, `redis=true`.
- `/ask` không key: 401.
- Cùng user, 10 request có key: 200; 5 request tiếp theo: 429.
- `history_length`: `0, 2, 4, 6, 8, 10, 12, 14, 16, 18`.

Output: [lần đầu](evidence/local-smoke.json),
[sau khi chuyển Docker](evidence/local-smoke-after-move.json).
Ảnh: [health local](screenshots/health-local.png).
Chưa chọn phương án fallback thay cho cloud; URL công khai vẫn cần bổ sung.

### Kết quả cloud còn cần bổ sung

Dán output của các lệnh trên vào đây:

```
(điền output)
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên platform
- `screenshots/health.png` — kết quả gọi `/health` từ trình duyệt hoặc curl

---

## Nếu Dùng Phương Án Dự Phòng

Không đăng ký được tài khoản cloud? Vẫn nộp được bài, nhưng CP5 tối đa 60% điểm:

1. Đặt `LOCAL_FALLBACK=true` trong `.env`
2. Chạy `docker compose up -d` rồi kiểm tra `docker compose ps`
3. Chụp màn hình vào `screenshots/`
4. Chạy `pytest tests/test_cp5.py -v` — bộ test sẽ tự chuyển sang kiểm tra
   `http://localhost:8000`
5. Ghi rõ lý do không deploy được vào phần dưới đây:

```
(điền lý do nếu dùng phương án dự phòng, ngược lại xóa mục này)
```

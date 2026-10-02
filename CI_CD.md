# CI/CD với GitHub Actions và Railway

Workflow `.github/workflows/ci.yml` chạy khi push hoặc mở/cập nhật pull request:

1. Cài Python 3.11 và dependencies, chạy test offline.
2. Khi test thành công, build Docker image để kiểm tra Dockerfile.
3. Khi cả test và build thành công, chỉ push trên `main` mới deploy Railway.

## Thiết lập một lần

- Trong Railway Project Settings, tạo **Project Token** cho environment cần deploy.
- Trong GitHub → Settings → Secrets and variables → Actions, tạo secret
  `RAILWAY_TOKEN` với token trên và variable `RAILWAY_SERVICE` với tên hoặc ID service ứng dụng (không chọn Redis).
- Tạo variable `PUBLIC_URL` là URL HTTPS công khai của service, dùng cho kiểm tra `/health` và `/ready` sau deploy.
- Workflow dùng GitHub environment `production`; nếu đặt secret/variable ở cấp environment, dùng đúng environment này.
- Trong Railway service, cấu hình `AGENT_API_KEY`, `REDIS_URL` và các biến ứng dụng cần thiết theo `.env.example`. Không đưa giá trị bí mật vào repo.
- Tắt automatic deployment từ GitHub trong Railway nếu đang bật, để push không deploy trực tiếp trước khi CI hoàn thành. Workflow sẽ upload source qua CLI.
- Push workflow lên GitHub và xem tab **Actions**. Badge trong README chỉ có trạng thái sau khi workflow chạy thật.

Image trong job build chỉ dùng để kiểm tra; Railway build lại cùng source bằng Dockerfile.
`railway up --ci` theo dõi build; workflow gọi `/health`, `/ready` với retry sau deploy.
Kiểm tra thêm trạng thái rollout trong Railway để xác nhận phiên bản vừa triển khai;
hai endpoint hiện chưa trả commit SHA nên smoke test chỉ xác nhận service đang phục vụ.
Health check của Railway tiếp tục dùng cấu hình trong `railway.toml`.

CI bỏ qua CP5 vì cần service đã deploy, các test Docker runtime và test badge trực tuyến để tránh phụ thuộc vào kết quả của chính workflow đang chạy.
Chạy kiểm tra triển khai riêng sau khi service hoạt động:

```bash
python -m pytest tests/test_cp5.py -v
```

Tham khảo: [Railway CLI deployment](https://docs.railway.com/cli/deploying),
[GitHub Actions cho Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

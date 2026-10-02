# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng placeholder dưới từng câu bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Văn Đại — Mã học viên: 2A202602477
>
> Bản nháp được hỗ trợ rà soát bằng AI. Học viên cần đọc, kiểm chứng và diễn đạt
> lại theo hiểu biết của mình trước khi nộp. Các mục chưa có quan sát thật được
> ghi rõ, không thay bằng số liệu giả.

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Ví dụ: khi tạo service mới trên cloud, quên đặt `AGENT_API_KEY`. Với trường bắt
buộc, `get_settings()` trong lifespan gây lỗi ngay lúc startup nên bản deploy
không được xem là khỏe. Nếu dùng mặc định `changeme`, service vẫn mở `/ask`
với một khóa ai đọc code cũng biết, có thể bị gọi trái phép và phát sinh chi phí.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Log thật từ agent-3 khi chạy stack ba agent, lấy từ `evidence/agent-smoke.txt`:

```json
{"user_id": "smoke-7736ccc1461e", "tokens_in": 3, "tokens_out": 35, "cost_usd": 2.145e-05, "event": "ask_completed", "level": "info", "timestamp": "2026-10-02T02:30:21.043855+00:00"}
```

1. Lọc theo `user_id`, `event` và `timestamp` để đối chiếu lượt gọi của một
   người dùng giữa các instance.
2. Cộng `cost_usd` hoặc thống kê `tokens_in`/`tokens_out` theo thời gian để
   theo dõi chi phí. Dòng print chung chung không có các trường này để tính.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (`Dockerfile.single`, dựa trên bản đầu của lab) | khoảng 1190 MB (`docker images` hiển thị 1.19GB) |
| Multi-stage | 218 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Đã build hai image với cùng `requirements.txt` và đo bằng
`docker images day12-agent`. Chênh lệch xấp xỉ 972 MB. Bản đầu dùng
`python:3.11` đầy đủ, mang theo nhiều công cụ/thư viện hệ điều hành phục vụ
build; bản mới dùng `python:3.11-slim`. Bản đầu còn giữ pip cache và copy
cả build context, bản mới tắt pip cache và chỉ copy virtualenv, `app`, `utils`.

Không thể quy toàn bộ phần giảm cho multi-stage: trong bài này việc đổi base
image sang slim đóng góp lớn, builder cũng không cài thêm compiler. Runtime
hiện vẫn chứa dependency test vì dùng chung `requirements.txt`.

Lệnh tái hiện:

```powershell
docker build -f Dockerfile.single -t day12-agent:single .
docker build -t day12-agent:prod .
docker images day12-agent
```

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Đã đổi comment trong `app/main.py`, build lại và lưu output tại
`evidence/build-cache.txt`: `COPY requirements.txt`, tạo virtualenv,
`pip install`, tạo user, `WORKDIR` và `COPY --from=builder` đều báo `CACHED`.
Hai bước `COPY app` và `COPY utils` báo `DONE`, không dùng cache.
Nếu `COPY . .` nằm trước
`RUN pip install`, thay đổi code làm mất cache của layer copy và bước pip
phải chạy lại dù `requirements.txt` không đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Một lỗ hổng thực thi mã có thể cho kẻ tấn công chạy lệnh với quyền của process
Python. Nếu process là root, kẻ đó có quyền root trong container; kết hợp thêm
lỗ hổng thoát container hoặc mount tài nguyên host không an toàn thì có thể
tác động tới host. Root trong container không tự động đồng nghĩa root trên host.
`USER app` làm process chạy với UID 10001, giảm quyền sửa file hệ thống và mức
thiệt hại khi app bị chiếm quyền; nó không thay thế việc vá lỗi hay giới hạn mount.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Tối đa 20 request: gửi 10 request ở giây 59 của phút trước, rồi 10 request ở
giây 00 của phút sau. Bộ đếm theo phút được reset giữa hai đợt nên cho cả hai
qua. Sliding window đếm 60 giây gần nhất, nên 10 request trước vẫn nằm trong
cửa sổ và đợt sau bị chặn. Redis sorted set dùng timestamp làm score và UUID
trong member để hai request cùng thời điểm không ghi đè nhau.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit chặn theo số request trong 60 giây, trả 429; cost guard chặn theo
chi phí tích lũy của user trong tháng UTC, trả 402.

Ví dụ user đã tiêu 10.01 USD với ngân sách 10 USD nhưng mới gọi request đầu
tiên trong phút: rate limit cho qua, cost guard chặn. Ngược lại, user mới tiêu
0.01 USD nhưng gọi request thứ 11 trong 60 giây: rate limit chặn dù còn tiền.

Trong code hiện tại, `/ask` kiểm tra chi phí đã ghi nhận trước khi gọi LLM,
rồi cộng chi phí thực tế sau khi gọi. Vì không giữ chỗ ngân sách, request làm
vượt ngưỡng vẫn có thể chạy; request sau mới bị chặn. Đây không phải giới hạn
chi tiêu tuyệt đối, nhất là khi có nhiều request đồng thời.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Redis mất kết nối → endpoint dùng chung trả lỗi ở cả ba container → readiness
loại các instance khỏi luồng traffic → nếu orchestrator dùng cùng endpoint
cho liveness, lỗi đủ ngưỡng sẽ kích hoạt restart → các instance mới vẫn không
nối được Redis nên tiếp tục lỗi. Khi Redis phục hồi, service còn phải chờ
startup và probe thành công, có thể kéo dài thời gian gián đoạn.

Tách `/health` chỉ kiểm tra process giúp tránh restart không cần thiết;
`/ready` trả 503 khi Redis lỗi để ngừng nhận traffic. Riêng Docker Compose
đánh dấu `unhealthy` không tự động restart chỉ vì healthcheck thất bại.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Đã chạy `docker compose up -d --build --scale agent=3`. Nginx giữ cổng 8000,
các agent dùng Redis chung. Với user `smoke-7736ccc1461e`, 10 request thành
công trả `history_length` lần lượt `0, 2, 4, 6, 8, 10, 12, 14, 16, 18`.
Log cùng user xuất hiện trên nhiều agent. Xem `evidence/local-smoke.json`
và `evidence/agent-smoke.txt`.

Trường này đếm message có trước lượt hỏi hiện tại; mỗi lượt thêm hai message.
Nếu dùng dict riêng từng process, request chuyển instance sẽ đọc một lịch sử
khác, nên số đếm có thể lặp hoặc giảm, ví dụ `0, 0, 0, 2, 2, 2` khi luân
phiên đều ba instance. Ví dụ dict là dự đoán, chưa thay code để đo.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> *Câu trả lời của bạn*

Chưa có URL và thông tin lỗi deploy cloud thực tế. Cần bổ sung thông báo lỗi,
cách đọc log để tìm nguyên nhân và cách sửa sau khi triển khai. Lỗi đầy ổ C
trong buổi kiểm tra local không được coi là lỗi cloud cho câu này.

"""CP4 — Graceful shutdown.

Khi dừng container hoặc triển khai phiên bản mới, hệ thống
thường gửi SIGTERM trước rồi mới dùng SIGKILL nếu process
không thoát trong thời gian cho phép.

Luồng xử lý:
    Nhận tín hiệu dừng.
    Đánh dấu service đang tắt.
    Chuyển tiếp tín hiệu cho handler của server.
    Server xử lý shutdown và các request đang chạy.
"""

from __future__ import annotations

import signal
import threading


class Lifecycle:
    """Giữ trạng thái vòng đời của process."""

    def __init__(self) -> None:
        self.shutting_down = False

        # Lưu handler đã đăng ký trước, ví dụ của Uvicorn.
        self._previous: dict = {}

    def request_shutdown(self, signum=None, frame=None) -> None:
        """Đánh dấu process đang tắt và gọi handler cũ.

        TODO (CP4):
          1. Đặt shutting_down = True.
          2. Lấy handler cũ theo signum.
          3. Nếu handler cũ gọi được, chuyển tiếp tín hiệu.

        Mỗi tín hiệu chỉ có một handler hiện hành.
        Nếu ghi đè handler Uvicorn nhưng không gọi lại,
        app có thể chỉ bật cờ mà không thực sự dừng server.

        Không thực hiện thao tác mạng hoặc công việc nặng
        trong signal handler.
        """

        self.shutting_down = True
        previous = self._previous.get(signum)

        # Tránh tự gọi lại chính handler này.
        if callable(previous) and previous != self.request_shutdown:
            previous(signum, frame)

    def install(self) -> None:
        """Đăng ký handler cho SIGTERM và SIGINT.

        TODO (CP4):
          1. Ghi nhớ handler cũ bằng signal.getsignal().
          2. Đăng ký request_shutdown bằng signal.signal().

        SIGTERM: yêu cầu dừng từ hệ thống.
        SIGINT: thường phát sinh khi nhấn Ctrl+C.

        Python chỉ cho đăng ký signal handler ở main thread.
        """

        if threading.current_thread() is not threading.main_thread():
            return

        for sig in (signal.SIGTERM, signal.SIGINT):
            previous = signal.getsignal(sig)

            # Không đăng ký lặp làm mất handler gốc.
            if previous != self.request_shutdown:
                self._previous[sig] = previous
                signal.signal(sig, self.request_shutdown)

    def restore(self) -> None:
        """Khôi phục handler cũ khi kết thúc lifespan.

        Chỉ khôi phục nếu handler hiện tại vẫn là handler
        của object này, tránh ghi đè handler của thành phần khác.
        """

        if threading.current_thread() is threading.main_thread():
            for sig, handler in self._previous.items():
                if signal.getsignal(sig) == self.request_shutdown:
                    signal.signal(sig, handler)

            self._previous.clear()


# Một instance dùng chung cho cả app.
lifecycle = Lifecycle()
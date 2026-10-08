"""Luồng nền chạy GA và truyền dữ liệu về giao diện qua Queue.

Quy tắc quan trọng: luồng nền KHÔNG được gọi trực tiếp widget Tkinter. Nó chỉ
đặt thông điệp vào `queue.Queue`; luồng giao diện sẽ lấy ra định kỳ bằng
`root.after(...)` rồi mới cập nhật widget. Nhờ vậy giao diện không bị đơ.

Module này không chứa logic GA; nó chỉ gọi `GeneticAlgorithm` trong ga/.
"""

from __future__ import annotations

import queue
import threading

from ga.algorithm import GAConfig, GeneticAlgorithm, ThongKeTheHe
from ga.data import BaiToan

# Các loại thông điệp gửi qua Queue, dạng tuple (loai, du_lieu).
THE_HE = "the_he"  # du_lieu: ThongKeTheHe
XONG = "xong"      # du_lieu: GAResult
LOI = "loi"        # du_lieu: str (nội dung lỗi)


class GAWorker:
    """Chạy một lần GA trong luồng nền (daemon).

    Mỗi lần chạy tạo một đối tượng GAWorker mới với Queue riêng, nên thông
    điệp của lần chạy cũ không thể lẫn sang lần chạy mới.
    """

    def __init__(self, cau_hinh: GAConfig, bai_toan: BaiToan, do_tre_ms: int = 0) -> None:
        """Khởi tạo worker.

        Tham số:
            cau_hinh: tham số GA đã được kiểm tra.
            bai_toan: bài toán TSP cần giải.
            do_tre_ms: độ trễ sau mỗi thế hệ (mili giây) để người xem kịp theo dõi.
                Độ trễ nằm ở luồng nền, không làm chậm giao diện.
        """
        self.cau_hinh = cau_hinh
        self.bai_toan = bai_toan
        self.do_tre_ms = max(0, do_tre_ms)
        self.hang_doi: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.stop_event = threading.Event()
        self._luong = threading.Thread(target=self._chay, daemon=True)

    def bat_dau(self) -> None:
        """Bắt đầu chạy GA ở luồng nền."""
        self._luong.start()

    def dung(self) -> None:
        """Yêu cầu GA dừng sau thế hệ hiện tại (kể cả khi đang chờ độ trễ)."""
        self.stop_event.set()

    @property
    def dang_chay(self) -> bool:
        """True nếu luồng nền vẫn đang hoạt động."""
        return self._luong.is_alive()

    def _chay(self) -> None:
        """Thân luồng nền: chạy GA và đưa kết quả/lỗi vào Queue."""
        try:
            ga = GeneticAlgorithm(
                self.cau_hinh,
                self.bai_toan.ma_tran,
                on_generation=self._sau_moi_the_he,
                stop_event=self.stop_event,
            )
            ket_qua = ga.chay()
            self.hang_doi.put((XONG, ket_qua))
        except Exception as loi:  # noqa: BLE001 - báo mọi lỗi về giao diện
            self.hang_doi.put((LOI, f"{type(loi).__name__}: {loi}"))

    def _sau_moi_the_he(self, thong_ke: ThongKeTheHe) -> None:
        """Callback của GA: gửi thống kê về giao diện rồi chờ độ trễ (nếu có)."""
        self.hang_doi.put((THE_HE, thong_ke))
        if self.do_tre_ms > 0:
            # wait() thay cho sleep() để nút Dừng có tác dụng ngay lập tức.
            self.stop_event.wait(self.do_tre_ms / 1000.0)

"""Vẽ hai biểu đồ Matplotlib nhúng trong giao diện Tkinter.

    1. Biểu đồ hội tụ: quãng đường tốt nhất (và trung bình) theo thế hệ.
    2. Bản đồ 2D: các địa điểm và tuyến đường tốt nhất, đánh số thứ tự ghé thăm.

Các hàm `ve_hoi_tu` và `ve_ban_do` chỉ làm việc với đối tượng Axes nên có thể
dùng độc lập (ví dụ lưu ảnh cho báo cáo). Lớp `BieuDo` gắn chúng vào Tkinter.
Module không chứa logic thuật toán GA.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Sequence

from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ga.data import BaiToan

# Bảng màu: ít màu, tương phản rõ, không dùng màu chỉ để trang trí.
MAU_TOT_NHAT = "#2563eb"   # xanh dương: quãng đường tốt nhất / tuyến đường
MAU_TRUNG_BINH = "#9ca3af"  # xám: đường trung bình (phụ, ít nổi bật)
MAU_DIEM_DAU = "#ea580c"   # cam: điểm xuất phát
MAU_CHU = "#111827"
MAU_CHU_PHU = "#6b7280"
MAU_LUOI = "#e5e7eb"

# Chỉ vẽ mũi tên và tên địa điểm khi số điểm không quá nhiều để tránh rối.
SO_DIEM_TOI_DA_VE_MUI_TEN = 40
SO_DIEM_TOI_DA_VE_TEN = 20


def _lam_dep_truc(ax: Axes) -> None:
    """Bỏ khung thừa, làm lưới và nhãn trục nhẹ nhàng (thông tin chính nổi bật hơn)."""
    for canh in ("top", "right"):
        ax.spines[canh].set_visible(False)
    for canh in ("left", "bottom"):
        ax.spines[canh].set_color(MAU_LUOI)
    ax.tick_params(colors=MAU_CHU_PHU, labelsize=8)
    ax.grid(True, color=MAU_LUOI, linewidth=0.6)
    ax.set_axisbelow(True)


def ve_hoi_tu(
    ax: Axes,
    lich_su_tot: Sequence[float],
    lich_su_tb: Sequence[float],
    tong_the_he: Optional[int] = None,
) -> None:
    """Vẽ biểu đồ hội tụ: quãng đường ngắn dần theo thế hệ.

    Tham số:
        ax: trục Matplotlib cần vẽ (sẽ bị xoá nội dung cũ).
        lich_su_tot: quãng đường tốt nhất tại từng thế hệ (phần tử 0 là quần thể khởi tạo).
        lich_su_tb: quãng đường trung bình tại từng thế hệ.
        tong_the_he: số thế hệ dự kiến; nếu có thì trục x cố định để đồ thị không bị co giãn khi đang chạy.
    """
    ax.clear()
    _lam_dep_truc(ax)
    ax.set_title("Hội tụ: quãng đường ngắn dần", fontsize=10, color=MAU_CHU, loc="left")
    ax.set_xlabel("Thế hệ", fontsize=9, color=MAU_CHU_PHU)
    ax.set_ylabel("Quãng đường (km)", fontsize=9, color=MAU_CHU_PHU)
    if tong_the_he:
        ax.set_xlim(0, tong_the_he)

    if not len(lich_su_tot):
        ax.text(0.5, 0.5, "Chưa có dữ liệu.\nBấm Chạy để bắt đầu.", ha="center", va="center",
                transform=ax.transAxes, color=MAU_CHU_PHU, fontsize=9)
        return

    x = range(len(lich_su_tot))
    ax.plot(x, lich_su_tb, color=MAU_TRUNG_BINH, linewidth=1.2, label="Trung bình quần thể")
    ax.plot(x, lich_su_tot, color=MAU_TOT_NHAT, linewidth=2, label="Tốt nhất")

    # Nhãn trực tiếp cho giá trị tốt nhất hiện tại (đồ thị tự giải thích, không cần dò trục).
    cuoi = len(lich_su_tot) - 1
    ax.plot([cuoi], [lich_su_tot[-1]], "o", color=MAU_TOT_NHAT, markersize=6,
            markeredgecolor="white", markeredgewidth=1.5)
    ax.annotate(f"{lich_su_tot[-1]:.3f} km", (cuoi, lich_su_tot[-1]), textcoords="offset points",
                xytext=(-6, 10), ha="right", fontsize=9, color=MAU_TOT_NHAT, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8, frameon=False, labelcolor=MAU_CHU)


def ve_ban_do(ax: Axes, bai_toan: BaiToan, tuyen: Optional[Sequence[int]] = None) -> None:
    """Vẽ bản đồ 2D các địa điểm và tuyến đường (nếu có).

    Trục x là kinh độ, trục y là vĩ độ. Tuyến là chu trình khép kín; điểm xuất
    phát màu cam, các điểm được đánh số theo thứ tự ghé thăm.

    Tham số:
        ax: trục Matplotlib cần vẽ (sẽ bị xoá nội dung cũ).
        bai_toan: bài toán chứa toạ độ và tên địa điểm.
        tuyen: hoán vị các chỉ số điểm; None nếu chưa có lời giải.
    """
    ax.clear()
    _lam_dep_truc(ax)
    toa_do = bai_toan.toa_do
    vi_do, kinh_do = toa_do[:, 0], toa_do[:, 1]
    n = bai_toan.so_diem

    # Tỷ lệ trục để bản đồ không bị méo (1° kinh độ ngắn hơn 1° vĩ độ ở vĩ độ ~21°).
    ax.set_aspect(1.0 / math.cos(math.radians(float(vi_do.mean()))), adjustable="datalim")
    ax.set_xlabel("Kinh độ", fontsize=9, color=MAU_CHU_PHU)
    ax.set_ylabel("Vĩ độ", fontsize=9, color=MAU_CHU_PHU)
    ax.tick_params(axis="x", labelrotation=30)
    if tuyen is None:
        ax.set_title("Bản đồ các địa điểm", fontsize=10, color=MAU_CHU, loc="left")
    else:
        ax.set_title("Tuyến đường tốt nhất", fontsize=10, color=MAU_CHU, loc="left")

    if tuyen is not None and len(tuyen) == n:
        vong = list(tuyen) + [tuyen[0]]
        if n <= SO_DIEM_TOI_DA_VE_MUI_TEN:
            for a, b in zip(vong, vong[1:]):
                ax.annotate("", xy=(kinh_do[b], vi_do[b]), xytext=(kinh_do[a], vi_do[a]),
                            arrowprops=dict(arrowstyle="-|>", color=MAU_TOT_NHAT, lw=1.6,
                                            shrinkA=7, shrinkB=7, mutation_scale=10),
                            zorder=2)
        else:
            ax.plot([kinh_do[i] for i in vong], [vi_do[i] for i in vong],
                    color=MAU_TOT_NHAT, linewidth=1.2, zorder=2)

    ax.scatter(kinh_do, vi_do, s=125 if n <= SO_DIEM_TOI_DA_VE_TEN else 18, color=MAU_CHU,
               edgecolors="white", linewidths=1.2, zorder=3)

    if tuyen is not None and len(tuyen) == n:
        d = tuyen[0]
        ax.scatter([kinh_do[d]], [vi_do[d]], s=140 if n <= SO_DIEM_TOI_DA_VE_TEN else 60,
                   marker="s", color=MAU_DIEM_DAU,
                   edgecolors="white", linewidths=1.2, zorder=4, label="Điểm xuất phát")
        ax.legend(loc="lower right", fontsize=8, frameon=False, labelcolor=MAU_CHU)
        if n <= SO_DIEM_TOI_DA_VE_TEN:
            for thu_tu, i in enumerate(tuyen, start=1):
                ax.annotate(str(thu_tu), (kinh_do[i], vi_do[i]), textcoords="offset points",
                            xytext=(0, 0), ha="center", va="center", fontsize=7.5,
                            color="white", fontweight="bold", zorder=5)

    ax.margins(0.15)
    if n <= SO_DIEM_TOI_DA_VE_TEN:
        so_bo = _dat_nhan_ten(ax, bai_toan)
        if so_bo:
            ax.text(0.01, 0.01, f"{so_bo} tên bị ẩn do các điểm quá gần nhau (xem trong log)",
                    transform=ax.transAxes, fontsize=7, color=MAU_CHU_PHU, va="bottom")


def _dat_nhan_ten(ax: Axes, bai_toan: BaiToan, co_chu: float = 7.0) -> int:
    """Đặt tên địa điểm cạnh mỗi điểm sao cho không đè lên nhau và không tràn khung.

    Với mỗi điểm, thử lần lượt 8 vị trí quanh nó (phải, trái, trên, dưới và 4 góc)
    và chọn vị trí đầu tiên không chạm nhãn đã đặt, không chạm ký hiệu điểm và nằm
    trọn trong khung biểu đồ. Nếu không có chỗ, bỏ nhãn (tên vẫn có trong log).
    Kích thước chữ được ước lượng theo số ký tự nên kết quả chỉ gần đúng.

    Tham số:
        ax: trục bản đồ (đã vẽ các điểm).
        bai_toan: bài toán chứa toạ độ và tên.
        co_chu: cỡ chữ của nhãn (pt).

    Trả về:
        Số nhãn bị bỏ vì không còn chỗ trống.
    """
    ax.apply_aspect()  # chốt giới hạn trục trước khi đổi sang toạ độ màn hình
    px_moi_pt = ax.figure.dpi / 72.0
    khung = ax.get_window_extent()
    diem = ax.transData.transform(bai_toan.toa_do[:, ::-1])  # (kinh độ, vĩ độ) -> pixel
    ban_kinh = 10 * px_moi_pt / 1.4  # nửa kích thước ký hiệu điểm (px) + đệm
    hop_da_dung = [(x - ban_kinh, y - ban_kinh, x + ban_kinh, y + ban_kinh) for x, y in diem]
    cao = co_chu * 1.35 * px_moi_pt

    def chong_nhau(a, b) -> bool:
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    so_bo = 0
    for i, ten in enumerate(bai_toan.ten_dia_diem):
        x, y = diem[i]
        rong = 0.58 * co_chu * len(ten) * px_moi_pt
        d = ban_kinh + 2
        # Góc dưới-trái (x0, y0) của hộp chữ cho từng hướng thử
        ung_vien = [
            (x + d, y - cao / 2), (x - d - rong, y - cao / 2),
            (x - rong / 2, y + d), (x - rong / 2, y - d - cao),
            (x + d * 0.7, y + d * 0.7), (x - d * 0.7 - rong, y + d * 0.7),
            (x + d * 0.7, y - d * 0.7 - cao), (x - d * 0.7 - rong, y - d * 0.7 - cao),
        ]
        for x0, y0 in ung_vien:
            hop = (x0, y0, x0 + rong, y0 + cao)
            trong_khung = hop[0] >= khung.x0 and hop[2] <= khung.x1 and hop[1] >= khung.y0 and hop[3] <= khung.y1
            if trong_khung and not any(chong_nhau(hop, h) for h in hop_da_dung):
                ax.annotate(ten, (bai_toan.toa_do[i, 1], bai_toan.toa_do[i, 0]),
                            textcoords="offset points", xytext=((x0 - x) / px_moi_pt, (y0 - y) / px_moi_pt),
                            ha="left", va="bottom", fontsize=co_chu, color=MAU_CHU_PHU, zorder=5)
                hop_da_dung.append(hop)
                break
        else:
            so_bo += 1
    return so_bo


class BieuDo:
    """Khung chứa hai biểu đồ (hội tụ và bản đồ) nhúng trong Tkinter."""

    def __init__(self, cha: tk.Misc) -> None:
        """Tạo Figure và gắn vào widget cha.

        Tham số:
            cha: widget Tkinter chứa biểu đồ (khung trong cửa sổ chính).
        """
        # Không dùng constrained_layout vì mỗi lần vẽ lại chậm hơn đáng kể; cố định lề thủ công.
        self.figure = Figure(figsize=(8, 4), dpi=100, facecolor="white")
        self.figure.subplots_adjust(left=0.09, right=0.98, bottom=0.2, top=0.92, wspace=0.3)
        self.ax_hoi_tu = self.figure.add_subplot(1, 2, 1)
        self.ax_ban_do = self.figure.add_subplot(1, 2, 2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=cha)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def hien_thi_bai_toan(self, bai_toan: BaiToan, tong_the_he: Optional[int] = None) -> None:
        """Đặt lại cả hai biểu đồ: chỉ hiện các địa điểm, chưa có tuyến/đường hội tụ."""
        ve_hoi_tu(self.ax_hoi_tu, [], [], tong_the_he)
        ve_ban_do(self.ax_ban_do, bai_toan, None)
        self.canvas.draw_idle()

    def cap_nhat(
        self,
        bai_toan: BaiToan,
        lich_su_tot: Sequence[float],
        lich_su_tb: Sequence[float],
        tuyen: Optional[Sequence[int]],
        tong_the_he: Optional[int] = None,
    ) -> None:
        """Vẽ lại cả hai biểu đồ với dữ liệu mới nhất (gọi khi đang chạy và khi xong)."""
        ve_hoi_tu(self.ax_hoi_tu, lich_su_tot, lich_su_tb, tong_the_he)
        ve_ban_do(self.ax_ban_do, bai_toan, tuyen)
        self.canvas.draw_idle()

    def luu_anh(self, duong_dan: str) -> None:
        """Lưu cả hai biểu đồ ra file ảnh (dùng cho báo cáo)."""
        self.figure.savefig(duong_dan, dpi=150)

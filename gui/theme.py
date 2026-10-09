"""Bảng màu và style (ttk) cho giao diện ứng dụng.

Tập trung mọi màu sắc ở một nơi để dễ chỉnh sửa. Bảng màu đồng bộ với hai
biểu đồ trong gui/plots.py (xanh dương là màu nhấn chính).
Module chỉ chứa phần trình bày, không có logic thuật toán.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# --- Bảng màu
NEN = "#f1f5f9"            # nền cửa sổ (xám xanh rất nhạt)
THE = "#ffffff"            # nền các khung (card)
VIEN = "#e2e8f0"           # đường viền nhẹ
XANH_DAM = "#1e293b"       # thanh tiêu đề, chữ đậm
CHU = "#0f172a"            # chữ chính
CHU_PHU = "#64748b"        # chữ phụ
NHAN = "#2563eb"           # màu nhấn chính (xanh dương, trùng màu đồ thị)
XANH_LA = "#16a34a"        # nút Chạy
XANH_LA_DAM = "#15803d"
DO = "#dc2626"             # nút Dừng
DO_DAM = "#b91c1c"
XAM = "#64748b"            # nút phụ (Đặt lại)
XAM_DAM = "#475569"
NHAN_DAM = "#1d4ed8"
VO_HIEU = "#cbd5e1"        # nút/ô bị vô hiệu hoá

# --- Màu của ô log (kiểu terminal nền tối)
LOG_NEN = "#0f172a"
LOG_CHU = "#e2e8f0"
LOG_MAU = {
    "tieu_de": "#38bdf8",   # === BẮT ĐẦU / HOÀN THÀNH === (xanh da trời)
    "khoi_tao": "#a78bfa",  # dòng khởi tạo quần thể (tím)
    "ky_luc": "#4ade80",    # kỷ lục mới (xanh lá)
    "tong_ket": "#fbbf24",  # tổng kết quãng đường, tuyến đường (vàng)
    "loi": "#f87171",       # lỗi (đỏ)
    "thuong": LOG_CHU,
}

FONT = ("Segoe UI", 10)
FONT_DAM = ("Segoe UI", 10, "bold")
FONT_MUC = ("Segoe UI", 9, "bold")
FONT_TIEU_DE = ("Segoe UI", 16, "bold")
FONT_PHU = ("Segoe UI", 9)
FONT_LOG = ("Consolas", 10)


def ap_dung_theme(goc: tk.Misc) -> None:
    """Áp dụng bảng màu và style cho toàn bộ widget ttk.

    Dùng theme "clam" vì cho phép tuỳ chỉnh màu nút, ô nhập, thanh tiến độ
    (theme mặc định của Windows bỏ qua phần lớn tuỳ chỉnh màu).

    Tham số:
        goc: cửa sổ gốc Tk.
    """
    goc.configure(background=NEN)
    s = ttk.Style(goc)
    s.theme_use("clam")

    s.configure(".", font=FONT, background=NEN, foreground=CHU)
    s.configure("TFrame", background=NEN)
    s.configure("The.TFrame", background=THE)
    s.configure("TLabel", background=NEN, foreground=CHU)
    s.configure("The.TLabel", background=THE, foreground=CHU)
    s.configure("Phu.TLabel", background=THE, foreground=CHU_PHU, font=FONT_PHU)
    s.configure("Muc.TLabel", background=THE, foreground=NHAN, font=FONT_MUC)
    s.configure("TrangThai.TLabel", background=NEN, foreground=XANH_DAM, font=FONT_DAM)

    # Khung chứa (card): nền trắng, viền mảnh, tiêu đề đậm
    s.configure("The.TLabelframe", background=THE, bordercolor=VIEN, lightcolor=VIEN,
                darkcolor=VIEN, relief="solid", borderwidth=1)
    s.configure("The.TLabelframe.Label", background=THE, foreground=XANH_DAM, font=FONT_DAM)

    s.configure("TSeparator", background=VIEN)

    # Ô nhập và danh sách chọn
    s.configure("TEntry", fieldbackground="white", bordercolor=VIEN, lightcolor=VIEN,
                darkcolor=VIEN, padding=4)
    s.map("TEntry",
          fieldbackground=[("disabled", "#f1f5f9")],
          foreground=[("disabled", "#94a3b8")],
          bordercolor=[("focus", NHAN)], lightcolor=[("focus", NHAN)])
    s.configure("TCombobox", fieldbackground="white", background="white", bordercolor=VIEN,
                lightcolor=VIEN, darkcolor=VIEN, arrowcolor=CHU_PHU, padding=4)
    s.map("TCombobox",
          fieldbackground=[("readonly", "white"), ("disabled", "#f1f5f9")],
          foreground=[("disabled", "#94a3b8")],
          arrowcolor=[("disabled", VO_HIEU)],
          bordercolor=[("focus", NHAN)])
    goc.option_add("*TCombobox*Listbox.background", "white")
    goc.option_add("*TCombobox*Listbox.selectBackground", NHAN)
    goc.option_add("*TCombobox*Listbox.font", FONT)

    # Các nút: mỗi nút một màu theo chức năng, đổi màu khi rê chuột/vô hiệu hoá
    def kieu_nut(ten: str, nen: str, nen_dam: str) -> None:
        """Tạo style nút `ten` với màu nền `nen`, màu khi rê chuột `nen_dam`."""
        s.configure(ten, background=nen, foreground="white", font=FONT_DAM, borderwidth=0,
                    focusthickness=0, focuscolor=nen, padding=(10, 7))
        s.map(ten,
              background=[("disabled", VO_HIEU), ("pressed", nen_dam), ("active", nen_dam)],
              foreground=[("disabled", "#f8fafc")])

    kieu_nut("Chay.TButton", XANH_LA, XANH_LA_DAM)
    kieu_nut("Dung.TButton", DO, DO_DAM)
    kieu_nut("Phu.TButton", XAM, XAM_DAM)
    kieu_nut("Nhan.TButton", NHAN, NHAN_DAM)

    s.configure("Xanh.Horizontal.TProgressbar", troughcolor="#dbeafe", background=NHAN,
                bordercolor=VIEN, lightcolor=NHAN, darkcolor=NHAN, thickness=14)

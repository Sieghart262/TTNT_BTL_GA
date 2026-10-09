"""Giao diện chính (Tkinter) của ứng dụng mô phỏng GA giải bài toán TSP.

Chức năng:
    - Nhập tham số GA và kiểm tra hợp lệ.
    - Chạy GA ở luồng nền (xem gui/worker.py), giao diện không bị đơ.
    - Hiển thị log thời gian thực trong ScrolledText.
    - Nút Chạy / Dừng / Đặt lại, thanh tiến độ, thanh trạng thái.
    - Hai biểu đồ nhúng trong giao diện (gui/plots.py): hội tụ fitness và bản đồ 2D.
Module này không chứa logic thuật toán GA.
"""

from __future__ import annotations

import math
import queue
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from ga.algorithm import (
    CHON_LOC_GIAI_DAU,
    CHON_LOC_ROULETTE,
    DOT_BIEN_INVERSION,
    DOT_BIEN_SWAP,
    GAConfig,
    GAResult,
    ThongKeTheHe,
)
from ga.data import BaiToan, bai_toan_ha_noi, bai_toan_ngau_nhien
from gui import worker as wk
from gui.plots import BieuDo
from gui.worker import GAWorker

NGUON_HA_NOI = "15 địa danh Hà Nội"
NGUON_NGAU_NHIEN = "N điểm ngẫu nhiên"
NHAN_CHON_LOC = {"Tournament (giải đấu)": CHON_LOC_GIAI_DAU, "Roulette (bánh xe)": CHON_LOC_ROULETTE}
NHAN_DOT_BIEN = {"Inversion (đảo đoạn)": DOT_BIEN_INVERSION, "Swap (hoán đổi)": DOT_BIEN_SWAP}

SO_THONG_DIEP_TOI_DA_MOI_LAN = 200  # giới hạn số thông điệp xử lý mỗi lần poll để UI luôn mượt
CHU_KY_POLL_MS = 40
KHOANG_VE_LAI_S = 0.4  # tối thiểu giữa 2 lần vẽ lại biểu đồ khi đang chạy (giây)
SO_DONG_LOG_TOI_DA = 600  # nếu nhiều thế hệ hơn thì log thưa bớt


# ---------------------------------------------------------------------------
# Các hàm đọc và kiểm tra dữ liệu nhập (không phụ thuộc widget, dễ kiểm thử)
# ---------------------------------------------------------------------------
def doc_so_nguyen(chuoi: str, ten: str, toi_thieu: int, toi_da: Optional[int] = None) -> int:
    """Đọc một số nguyên từ chuỗi nhập; ném ValueError (tiếng Việt) nếu sai.

    Tham số:
        chuoi: nội dung ô nhập.
        ten: tên tham số, dùng trong thông báo lỗi.
        toi_thieu, toi_da: khoảng giá trị cho phép (toi_da=None là không giới hạn).
    """
    try:
        gia_tri = int(chuoi.strip())
    except ValueError:
        raise ValueError(f"{ten} phải là số nguyên.") from None
    if gia_tri < toi_thieu or (toi_da is not None and gia_tri > toi_da):
        khoang = f">= {toi_thieu}" if toi_da is None else f"trong khoảng [{toi_thieu}, {toi_da}]"
        raise ValueError(f"{ten} phải {khoang}.")
    return gia_tri


def doc_so_thuc(chuoi: str, ten: str, toi_thieu: float, toi_da: float) -> float:
    """Đọc một số thực trong [toi_thieu, toi_da]; chấp nhận cả dấu phẩy thập phân."""
    try:
        gia_tri = float(chuoi.strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{ten} phải là số thực.") from None
    if not math.isfinite(gia_tri) or not toi_thieu <= gia_tri <= toi_da:
        raise ValueError(f"{ten} phải nằm trong khoảng [{toi_thieu}, {toi_da}].")
    return gia_tri


def doc_seed(chuoi: str) -> Optional[int]:
    """Đọc seed; để trống nghĩa là không cố định seed (trả về None)."""
    if not chuoi.strip():
        return None
    return doc_so_nguyen(chuoi, "Seed", -(2**31), 2**31 - 1)


# ---------------------------------------------------------------------------
# Ứng dụng
# ---------------------------------------------------------------------------
class UngDungGA:
    """Cửa sổ chính của ứng dụng."""

    def __init__(self, goc: tk.Tk) -> None:
        """Dựng giao diện.

        Tham số:
            goc: cửa sổ gốc Tk.
        """
        self.goc = goc
        goc.title("Mô phỏng Giải thuật di truyền - Bài toán người chào hàng (TSP)")
        goc.geometry("1150x760")
        goc.minsize(900, 600)

        self.worker: Optional[GAWorker] = None
        self.bai_toan: BaiToan = bai_toan_ha_noi()
        self.ket_qua: Optional[GAResult] = None
        self.buoc_log = 1
        self.tong_the_he = 0
        # Dữ liệu biểu đồ tích luỹ trong lúc chạy
        self.ls_tot: list[float] = []
        self.ls_tb: list[float] = []
        self.tuyen_hien_tai: Optional[list[int]] = None
        self.can_ve_lai = False
        self.lan_ve_cuoi = 0.0

        self._tao_bien()
        self._dung_giao_dien()
        self._cap_nhat_trang_thai_nut(dang_chay=False)
        self._khi_doi_nguon_bai_toan()
        self.bieu_do.hien_thi_bai_toan(self.bai_toan)
        goc.protocol("WM_DELETE_WINDOW", self._khi_dong_cua_so)

    # ------------------------------------------------------------ dựng UI
    def _tao_bien(self) -> None:
        """Tạo các biến Tkinter gắn với ô nhập."""
        self.v_so_ca_the = tk.StringVar(value="100")
        self.v_so_the_he = tk.StringVar(value="300")
        self.v_ty_le_dot_bien = tk.StringVar(value="0.05")
        self.v_ty_le_lai_ghep = tk.StringVar(value="0.85")
        self.v_do_tre = tk.StringVar(value="30")
        self.v_seed = tk.StringVar(value="")
        self.v_nguon = tk.StringVar(value=NGUON_HA_NOI)
        self.v_so_diem = tk.StringVar(value="30")
        self.v_chon_loc = tk.StringVar(value=next(iter(NHAN_CHON_LOC)))
        self.v_dot_bien = tk.StringVar(value=next(iter(NHAN_DOT_BIEN)))
        self.v_trang_thai = tk.StringVar(value="Sẵn sàng.")

    def _dung_giao_dien(self) -> None:
        """Bố cục: tham số (trái) | biểu đồ (phải) | log (dưới) | trạng thái."""
        self.goc.columnconfigure(1, weight=1)
        self.goc.rowconfigure(0, weight=3)
        self.goc.rowconfigure(1, weight=2)

        # --- Khung tham số
        khung_tham_so = ttk.LabelFrame(self.goc, text="Tham số", padding=10)
        khung_tham_so.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=(8, 4))

        dong = 0
        self.o_nhap: dict[str, ttk.Widget] = {}
        for nhan, bien, khoa in [
            ("Số cá thể", self.v_so_ca_the, "so_ca_the"),
            ("Số thế hệ", self.v_so_the_he, "so_the_he"),
            ("Tỷ lệ đột biến (0-1)", self.v_ty_le_dot_bien, "ty_le_dot_bien"),
            ("Tỷ lệ lai ghép (0-1)", self.v_ty_le_lai_ghep, "ty_le_lai_ghep"),
        ]:
            ttk.Label(khung_tham_so, text=nhan).grid(row=dong, column=0, sticky="w", pady=2)
            o = ttk.Entry(khung_tham_so, textvariable=bien, width=12)
            o.grid(row=dong, column=1, sticky="e", pady=2)
            self.o_nhap[khoa] = o
            dong += 1

        ttk.Separator(khung_tham_so).grid(row=dong, column=0, columnspan=2, sticky="ew", pady=6)
        dong += 1

        ttk.Label(khung_tham_so, text="Chọn lọc").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_chon_loc = ttk.Combobox(
            khung_tham_so, textvariable=self.v_chon_loc, values=list(NHAN_CHON_LOC),
            state="readonly", width=20,
        )
        self.o_chon_loc.grid(row=dong, column=1, sticky="e", pady=2)
        dong += 1
        ttk.Label(khung_tham_so, text="Đột biến").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_dot_bien = ttk.Combobox(
            khung_tham_so, textvariable=self.v_dot_bien, values=list(NHAN_DOT_BIEN),
            state="readonly", width=20,
        )
        self.o_dot_bien.grid(row=dong, column=1, sticky="e", pady=2)
        dong += 1
        ttk.Label(khung_tham_so, text="Độ trễ/thế hệ (ms)").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_do_tre = ttk.Entry(khung_tham_so, textvariable=self.v_do_tre, width=12)
        self.o_do_tre.grid(row=dong, column=1, sticky="e", pady=2)
        dong += 1
        ttk.Label(khung_tham_so, text="Seed (trống = ngẫu nhiên)").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_seed = ttk.Entry(khung_tham_so, textvariable=self.v_seed, width=12)
        self.o_seed.grid(row=dong, column=1, sticky="e", pady=2)
        dong += 1

        ttk.Separator(khung_tham_so).grid(row=dong, column=0, columnspan=2, sticky="ew", pady=6)
        dong += 1

        ttk.Label(khung_tham_so, text="Bài toán").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_nguon = ttk.Combobox(
            khung_tham_so, textvariable=self.v_nguon, values=[NGUON_HA_NOI, NGUON_NGAU_NHIEN],
            state="readonly", width=20,
        )
        self.o_nguon.grid(row=dong, column=1, sticky="e", pady=2)
        self.o_nguon.bind("<<ComboboxSelected>>", lambda _e: self._khi_doi_nguon_bai_toan())
        dong += 1
        ttk.Label(khung_tham_so, text="Số điểm N (3-200)").grid(row=dong, column=0, sticky="w", pady=2)
        self.o_so_diem = ttk.Entry(khung_tham_so, textvariable=self.v_so_diem, width=12)
        self.o_so_diem.grid(row=dong, column=1, sticky="e", pady=2)
        dong += 1

        khung_nut = ttk.Frame(khung_tham_so)
        khung_nut.grid(row=dong, column=0, columnspan=2, pady=(12, 0), sticky="ew")
        self.nut_chay = ttk.Button(khung_nut, text="Chạy", command=self.bat_dau_chay)
        self.nut_dung = ttk.Button(khung_nut, text="Dừng", command=self.dung_chay)
        self.nut_dat_lai = ttk.Button(khung_nut, text="Đặt lại", command=self.dat_lai)
        for nut in (self.nut_chay, self.nut_dung, self.nut_dat_lai):
            nut.pack(side="left", expand=True, fill="x", padx=2)
        self.nut_luu_anh = ttk.Button(khung_tham_so, text="Lưu ảnh biểu đồ", command=self.luu_anh_bieu_do)
        self.nut_luu_anh.grid(row=dong + 1, column=0, columnspan=2, pady=(6, 0), sticky="ew", padx=2)

        # --- Khung biểu đồ
        self.khung_bieu_do = ttk.LabelFrame(self.goc, text="Biểu đồ", padding=4)
        self.khung_bieu_do.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=(8, 4))
        self.bieu_do = BieuDo(self.khung_bieu_do)

        # --- Log
        khung_log = ttk.LabelFrame(self.goc, text="Log thời gian thực", padding=6)
        khung_log.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)
        khung_log.rowconfigure(0, weight=1)
        khung_log.columnconfigure(0, weight=1)
        self.o_log = scrolledtext.ScrolledText(
            khung_log, height=10, state="disabled", wrap="word", font=("Consolas", 10)
        )
        self.o_log.grid(row=0, column=0, sticky="nsew")

        # --- Thanh trạng thái
        khung_tt = ttk.Frame(self.goc)
        khung_tt.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        khung_tt.columnconfigure(1, weight=1)
        ttk.Label(khung_tt, textvariable=self.v_trang_thai).grid(row=0, column=0, sticky="w")
        self.thanh_tien_do = ttk.Progressbar(khung_tt, mode="determinate", length=300)
        self.thanh_tien_do.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------ trạng thái UI
    def _cap_nhat_trang_thai_nut(self, dang_chay: bool) -> None:
        """Bật/tắt các nút và ô nhập theo việc GA đang chạy hay không."""
        bat = "disabled" if dang_chay else "normal"
        for o in self.o_nhap.values():
            o.configure(state=bat)
        self.o_do_tre.configure(state=bat)
        self.o_seed.configure(state=bat)
        doc_chon = "disabled" if dang_chay else "readonly"
        for o in (self.o_chon_loc, self.o_dot_bien, self.o_nguon):
            o.configure(state=doc_chon)
        self.nut_chay.configure(state=bat)
        self.nut_dat_lai.configure(state=bat)
        self.nut_dung.configure(state="normal" if dang_chay else "disabled")
        co_ket_qua = not dang_chay and self.ket_qua is not None
        self.nut_luu_anh.configure(state="normal" if co_ket_qua else "disabled")
        if not dang_chay:
            self._khi_doi_nguon_bai_toan()
        else:
            self.o_so_diem.configure(state="disabled")

    def _khi_doi_nguon_bai_toan(self) -> None:
        """Chỉ cho nhập N khi chọn bài toán N điểm ngẫu nhiên."""
        ngau_nhien = self.v_nguon.get() == NGUON_NGAU_NHIEN
        self.o_so_diem.configure(state="normal" if ngau_nhien else "disabled")

    # ------------------------------------------------------------ log
    def ghi_log(self, noi_dung: str) -> None:
        """Thêm một dòng vào ô log và tự cuộn xuống cuối."""
        self.o_log.configure(state="normal")
        self.o_log.insert("end", noi_dung + "\n")
        self.o_log.see("end")
        self.o_log.configure(state="disabled")

    def _xoa_log(self) -> None:
        """Xoá toàn bộ nội dung log."""
        self.o_log.configure(state="normal")
        self.o_log.delete("1.0", "end")
        self.o_log.configure(state="disabled")

    # ------------------------------------------------------------ điều khiển
    def _doc_tham_so(self) -> tuple[GAConfig, int, BaiToan]:
        """Đọc và kiểm tra toàn bộ ô nhập.

        Trả về:
            (cấu hình GA, độ trễ ms, bài toán).

        Ngoại lệ:
            ValueError với thông báo tiếng Việt khi dữ liệu không hợp lệ.
        """
        so_ca_the = doc_so_nguyen(self.v_so_ca_the.get(), "Số cá thể", 2, 5000)
        so_the_he = doc_so_nguyen(self.v_so_the_he.get(), "Số thế hệ", 1, 100000)
        ty_le_dot_bien = doc_so_thuc(self.v_ty_le_dot_bien.get(), "Tỷ lệ đột biến", 0.0, 1.0)
        ty_le_lai_ghep = doc_so_thuc(self.v_ty_le_lai_ghep.get(), "Tỷ lệ lai ghép", 0.0, 1.0)
        do_tre = doc_so_nguyen(self.v_do_tre.get(), "Độ trễ", 0, 5000)
        seed = doc_seed(self.v_seed.get())

        cau_hinh = GAConfig(
            so_ca_the=so_ca_the,
            so_the_he=so_the_he,
            ty_le_dot_bien=ty_le_dot_bien,
            ty_le_lai_ghep=ty_le_lai_ghep,
            so_elite=min(2, so_ca_the - 1),
            phuong_phap_chon=NHAN_CHON_LOC[self.v_chon_loc.get()],
            phuong_phap_dot_bien=NHAN_DOT_BIEN[self.v_dot_bien.get()],
            seed=seed,
        )
        cau_hinh.kiem_tra()

        if self.v_nguon.get() == NGUON_NGAU_NHIEN:
            n = doc_so_nguyen(self.v_so_diem.get(), "Số điểm N", 3, 200)
            bai_toan = bai_toan_ngau_nhien(n, seed)
        else:
            bai_toan = bai_toan_ha_noi()
        return cau_hinh, do_tre, bai_toan

    def bat_dau_chay(self) -> None:
        """Xử lý nút Chạy: kiểm tra tham số rồi khởi động luồng nền."""
        try:
            cau_hinh, do_tre, bai_toan = self._doc_tham_so()
        except ValueError as loi:
            messagebox.showerror("Tham số không hợp lệ", str(loi), parent=self.goc)
            return

        self._xoa_log()
        self.bai_toan = bai_toan
        self.ket_qua = None
        self.tong_the_he = cau_hinh.so_the_he
        self.buoc_log = max(1, math.ceil(cau_hinh.so_the_he / SO_DONG_LOG_TOI_DA))
        self.thanh_tien_do.configure(maximum=cau_hinh.so_the_he, value=0)
        self._xoa_du_lieu_bieu_do()
        self.bieu_do.hien_thi_bai_toan(bai_toan, cau_hinh.so_the_he)

        self.ghi_log("=== BẮT ĐẦU CHẠY GA ===")
        self.ghi_log(
            f"Bài toán: {bai_toan.so_diem} điểm | Quần thể: {cau_hinh.so_ca_the} | "
            f"Số thế hệ: {cau_hinh.so_the_he}"
        )
        self.ghi_log(
            f"Lai ghép OX: {cau_hinh.ty_le_lai_ghep} | Đột biến: {cau_hinh.ty_le_dot_bien} "
            f"({self.v_dot_bien.get()}) | Chọn lọc: {self.v_chon_loc.get()} | "
            f"Elite: {cau_hinh.so_elite} | Seed: {cau_hinh.seed if cau_hinh.seed is not None else 'ngẫu nhiên'}"
        )
        if self.buoc_log > 1:
            self.ghi_log(f"(Nhiều thế hệ nên log ghi thưa: mỗi {self.buoc_log} thế hệ và mỗi lần có kỷ lục mới)")

        self.worker = GAWorker(cau_hinh, bai_toan, do_tre)
        self.worker.bat_dau()
        self._cap_nhat_trang_thai_nut(dang_chay=True)
        self.v_trang_thai.set("Đang chạy...")
        self.goc.after(CHU_KY_POLL_MS, self._lay_thong_diep)

    def dung_chay(self) -> None:
        """Xử lý nút Dừng: yêu cầu luồng nền dừng sau thế hệ hiện tại."""
        if self.worker is not None:
            self.worker.dung()
            self.v_trang_thai.set("Đang dừng...")
            self.nut_dung.configure(state="disabled")

    def dat_lai(self) -> None:
        """Xử lý nút Đặt lại: xoá log, tiến độ và kết quả."""
        self._xoa_log()
        self.ket_qua = None
        self.thanh_tien_do.configure(value=0)
        self._xoa_du_lieu_bieu_do()
        self.bieu_do.hien_thi_bai_toan(self.bai_toan)
        self.v_trang_thai.set("Sẵn sàng.")
        self._cap_nhat_trang_thai_nut(dang_chay=False)

    def luu_anh_bieu_do(self) -> None:
        """Xử lý nút Lưu ảnh: lưu hai biểu đồ hiện tại ra file PNG để đưa vào báo cáo."""
        duong_dan = filedialog.asksaveasfilename(
            parent=self.goc, title="Lưu ảnh biểu đồ", defaultextension=".png",
            filetypes=[("Ảnh PNG", "*.png"), ("Ảnh PDF", "*.pdf")], initialfile="bieu_do_ga.png",
        )
        if not duong_dan:
            return
        try:
            self.bieu_do.luu_anh(duong_dan)
        except OSError as loi:
            messagebox.showerror("Không lưu được ảnh", str(loi), parent=self.goc)
            return
        self.ghi_log(f"Đã lưu ảnh biểu đồ: {duong_dan}")

    def _xoa_du_lieu_bieu_do(self) -> None:
        """Xoá dữ liệu biểu đồ tích luỹ của lần chạy trước."""
        self.ls_tot = []
        self.ls_tb = []
        self.tuyen_hien_tai = None
        self.can_ve_lai = False

    def _ve_lai_bieu_do(self, ket_thuc: bool = False) -> None:
        """Vẽ lại biểu đồ nếu có dữ liệu mới, giới hạn tần suất khi đang chạy.

        Tham số:
            ket_thuc: True khi GA đã xong - luôn vẽ đầy đủ, bỏ qua giới hạn tần suất.
        """
        bay_gio = time.monotonic()
        if not self.can_ve_lai or (not ket_thuc and bay_gio - self.lan_ve_cuoi < KHOANG_VE_LAI_S):
            return
        self.bieu_do.cap_nhat(self.bai_toan, self.ls_tot, self.ls_tb, self.tuyen_hien_tai, self.tong_the_he)
        self.can_ve_lai = False
        self.lan_ve_cuoi = bay_gio

    # ------------------------------------------------------------ nhận dữ liệu từ luồng nền
    def _lay_thong_diep(self) -> None:
        """Lấy các thông điệp từ Queue của worker và cập nhật giao diện.

        Chạy trong luồng giao diện, được lập lịch bằng `after`, nên an toàn
        để thao tác với widget Tkinter.
        """
        if self.worker is None:
            return
        ket_thuc = False
        for _ in range(SO_THONG_DIEP_TOI_DA_MOI_LAN):
            try:
                loai, du_lieu = self.worker.hang_doi.get_nowait()
            except queue.Empty:
                break
            if loai == wk.THE_HE:
                self._xu_ly_the_he(du_lieu)  # type: ignore[arg-type]
            elif loai == wk.XONG:
                self._xu_ly_xong(du_lieu)  # type: ignore[arg-type]
                ket_thuc = True
            elif loai == wk.LOI:
                self._xu_ly_loi(str(du_lieu))
                ket_thuc = True
        self._ve_lai_bieu_do()
        if ket_thuc:
            self.worker = None
            self._cap_nhat_trang_thai_nut(dang_chay=False)
        else:
            self.goc.after(CHU_KY_POLL_MS, self._lay_thong_diep)

    def _xu_ly_the_he(self, tk_: ThongKeTheHe) -> None:
        """Ghi log và cập nhật tiến độ cho một thế hệ."""
        self.thanh_tien_do.configure(value=tk_.the_he)
        self.ls_tot.append(tk_.tot_nhat)
        self.ls_tb.append(tk_.trung_binh)
        if tk_.cai_thien or self.tuyen_hien_tai is None:
            self.tuyen_hien_tai = tk_.tuyen_tot_nhat
        self.can_ve_lai = True
        if tk_.the_he == 0:
            self.ghi_log(f"[Khởi tạo] Quần thể ngẫu nhiên | Tốt nhất: {tk_.tot_nhat:.3f} km | TB: {tk_.trung_binh:.3f} km")
        elif tk_.the_he % self.buoc_log == 0 or tk_.cai_thien or tk_.the_he == self.tong_the_he:
            dau = " ★ kỷ lục mới" if tk_.cai_thien else ""
            self.ghi_log(
                f"[Thế hệ {tk_.the_he}/{self.tong_the_he}] Tốt nhất: {tk_.tot_nhat:.3f} km | "
                f"TB: {tk_.trung_binh:.3f} km | Lai ghép: {tk_.so_lai_ghep} | "
                f"Đột biến: {tk_.so_dot_bien}{dau}"
            )
        self.v_trang_thai.set(f"Thế hệ {tk_.the_he}/{self.tong_the_he} - Tốt nhất: {tk_.tot_nhat:.3f} km")

    def _xu_ly_xong(self, ket_qua: GAResult) -> None:
        """Hiển thị tổng kết khi GA kết thúc (hoặc bị dừng)."""
        self.ket_qua = ket_qua
        self.ls_tot = list(ket_qua.lich_su_tot_nhat)
        self.ls_tb = list(ket_qua.lich_su_trung_binh)
        self.tuyen_hien_tai = ket_qua.tuyen_tot_nhat
        self.can_ve_lai = True
        self._ve_lai_bieu_do(ket_thuc=True)
        ten = self.bai_toan.ten_dia_diem
        tuyen = ket_qua.tuyen_tot_nhat
        self.ghi_log("=== BỊ DỪNG SỚM ===" if ket_qua.bi_dung else "=== HOÀN THÀNH ===")
        self.ghi_log(f"Số thế hệ đã chạy: {ket_qua.so_the_he_da_chay} | Thời gian: {ket_qua.thoi_gian_chay:.2f} giây")
        self.ghi_log(
            f"Quãng đường: {ket_qua.lich_su_tot_nhat[0]:.3f} km (khởi tạo) -> "
            f"{ket_qua.quang_duong_tot_nhat:.3f} km (tốt nhất)"
        )
        self.ghi_log("Tuyến đường: " + " -> ".join(ten[i] for i in tuyen) + f" -> {ten[tuyen[0]]}")
        self.v_trang_thai.set(
            ("Đã dừng. " if ket_qua.bi_dung else "Hoàn thành. ")
            + f"Tốt nhất: {ket_qua.quang_duong_tot_nhat:.3f} km"
        )

    def _xu_ly_loi(self, noi_dung: str) -> None:
        """Hiển thị lỗi xảy ra trong luồng nền."""
        self.ghi_log(f"!!! LỖI: {noi_dung}")
        self.v_trang_thai.set("Có lỗi xảy ra.")
        messagebox.showerror("Lỗi khi chạy GA", noi_dung, parent=self.goc)

    # ------------------------------------------------------------ đóng cửa sổ
    def _khi_dong_cua_so(self) -> None:
        """Dừng luồng nền (nếu có) rồi đóng cửa sổ."""
        if self.worker is not None:
            self.worker.dung()
        self.goc.destroy()

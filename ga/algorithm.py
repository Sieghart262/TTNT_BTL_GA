"""Thuật toán di truyền (GA) giải bài toán người chào hàng (TSP).

Module này chứa toàn bộ vòng lặp tiến hoá và hoàn toàn độc lập với giao diện:
không import tkinter hay matplotlib. Giao diện nhận thông tin từng thế hệ
qua callback `on_generation` và có thể yêu cầu dừng qua `threading.Event`.

Quy trình mỗi thế hệ:
    1. Đánh giá fitness của cả quần thể.
    2. Giữ lại các cá thể ưu tú (elitism).
    3. Chọn lọc cha mẹ -> lai ghép (OX) -> đột biến để sinh quần thể mới.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from ga import operators as op
from ga.data import tinh_tong_quang_duong

CHON_LOC_GIAI_DAU = "tournament"
CHON_LOC_ROULETTE = "roulette"
DOT_BIEN_INVERSION = "inversion"
DOT_BIEN_SWAP = "swap"


@dataclass
class GAConfig:
    """Tham số cấu hình của GA.

    Thuộc tính:
        so_ca_the: số cá thể trong quần thể.
        so_the_he: số thế hệ tối đa.
        ty_le_dot_bien: xác suất đột biến của mỗi cá thể con, trong [0, 1].
        ty_le_lai_ghep: xác suất lai ghép của mỗi cặp cha mẹ, trong [0, 1].
        so_elite: số cá thể tốt nhất được giữ nguyên sang thế hệ sau.
        kich_thuoc_giai: kích thước giải đấu (khi dùng Tournament).
        phuong_phap_chon: "tournament" hoặc "roulette".
        phuong_phap_dot_bien: "inversion" hoặc "swap".
        seed: hạt giống ngẫu nhiên để tái lập kết quả (None = ngẫu nhiên).
    """

    so_ca_the: int = 100
    so_the_he: int = 300
    ty_le_dot_bien: float = 0.05
    ty_le_lai_ghep: float = 0.85
    so_elite: int = 2
    kich_thuoc_giai: int = 3
    phuong_phap_chon: str = CHON_LOC_GIAI_DAU
    phuong_phap_dot_bien: str = DOT_BIEN_INVERSION
    seed: Optional[int] = None

    def kiem_tra(self) -> None:
        """Kiểm tra tính hợp lệ của tham số; ném ValueError kèm thông báo tiếng Việt."""
        if self.so_ca_the < 2:
            raise ValueError("Số cá thể phải >= 2.")
        if self.so_the_he < 1:
            raise ValueError("Số thế hệ phải >= 1.")
        if not 0.0 <= self.ty_le_dot_bien <= 1.0:
            raise ValueError("Tỷ lệ đột biến phải nằm trong khoảng [0, 1].")
        if not 0.0 <= self.ty_le_lai_ghep <= 1.0:
            raise ValueError("Tỷ lệ lai ghép phải nằm trong khoảng [0, 1].")
        if not 0 <= self.so_elite < self.so_ca_the:
            raise ValueError("Số cá thể elite phải trong khoảng [0, số cá thể - 1].")
        if self.kich_thuoc_giai < 1:
            raise ValueError("Kích thước giải đấu phải >= 1.")
        if self.phuong_phap_chon not in (CHON_LOC_GIAI_DAU, CHON_LOC_ROULETTE):
            raise ValueError("Phương pháp chọn lọc không hợp lệ.")
        if self.phuong_phap_dot_bien not in (DOT_BIEN_INVERSION, DOT_BIEN_SWAP):
            raise ValueError("Phương pháp đột biến không hợp lệ.")


@dataclass
class ThongKeTheHe:
    """Thông tin của một thế hệ, gửi cho giao diện qua callback.

    Thuộc tính:
        the_he: số thứ tự thế hệ (0 là quần thể khởi tạo).
        tot_nhat: quãng đường ngắn nhất trong thế hệ này (km).
        trung_binh: quãng đường trung bình của quần thể (km).
        tuyen_tot_nhat: tuyến đường tốt nhất của thế hệ này.
        so_lai_ghep: số cặp được lai ghép trong lần sinh ra thế hệ này.
        so_dot_bien: số cá thể con bị đột biến.
        cai_thien: True nếu tốt hơn mọi thế hệ trước (kỷ lục mới).
    """

    the_he: int
    tot_nhat: float
    trung_binh: float
    tuyen_tot_nhat: list[int]
    so_lai_ghep: int = 0
    so_dot_bien: int = 0
    cai_thien: bool = False


@dataclass
class GAResult:
    """Kết quả cuối cùng của một lần chạy GA.

    Thuộc tính:
        tuyen_tot_nhat: tuyến đường ngắn nhất tìm được.
        quang_duong_tot_nhat: độ dài tuyến đó (km).
        lich_su_tot_nhat: quãng đường tốt nhất theo từng thế hệ (đồ thị hội tụ).
        lich_su_trung_binh: quãng đường trung bình theo từng thế hệ.
        so_the_he_da_chay: số thế hệ đã tiến hoá (không tính quần thể khởi tạo).
        bi_dung: True nếu người dùng yêu cầu dừng sớm.
        thoi_gian_chay: thời gian chạy (giây).
    """

    tuyen_tot_nhat: list[int]
    quang_duong_tot_nhat: float
    lich_su_tot_nhat: list[float] = field(default_factory=list)
    lich_su_trung_binh: list[float] = field(default_factory=list)
    so_the_he_da_chay: int = 0
    bi_dung: bool = False
    thoi_gian_chay: float = 0.0


class GeneticAlgorithm:
    """Giải thuật di truyền cho TSP.

    Ví dụ:
        ga = GeneticAlgorithm(GAConfig(seed=1), tao_ma_tran_khoang_cach())
        ket_qua = ga.chay()
    """

    def __init__(
        self,
        cau_hinh: GAConfig,
        ma_tran: np.ndarray,
        on_generation: Optional[Callable[[ThongKeTheHe], None]] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> None:
        """Khởi tạo bộ giải.

        Tham số:
            cau_hinh: tham số GA (sẽ được kiểm tra hợp lệ).
            ma_tran: ma trận khoảng cách (km) giữa các địa điểm.
            on_generation: hàm được gọi sau mỗi thế hệ với `ThongKeTheHe`.
                Hàm này chạy trong cùng luồng với GA nên phải thật nhẹ;
                giao diện chỉ nên đẩy dữ liệu vào Queue.
            stop_event: khi được set, GA dừng sau thế hệ hiện tại.
        """
        cau_hinh.kiem_tra()
        if ma_tran.shape[0] < 3:
            raise ValueError("Cần ít nhất 3 địa điểm.")
        self.cau_hinh = cau_hinh
        self.ma_tran = ma_tran
        self.on_generation = on_generation
        self.stop_event = stop_event
        self.rng = random.Random(cau_hinh.seed)

    def chay(self) -> GAResult:
        """Chạy vòng lặp tiến hoá và trả về kết quả.

        Trả về:
            GAResult chứa tuyến tốt nhất và lịch sử hội tụ.
        """
        cfg = self.cau_hinh
        bat_dau = time.perf_counter()
        so_diem = self.ma_tran.shape[0]

        quan_the = op.tao_quan_the(cfg.so_ca_the, so_diem, self.rng)
        fitness = self._danh_gia(quan_the)

        ket_qua = GAResult(tuyen_tot_nhat=[], quang_duong_tot_nhat=float("inf"))
        self._ghi_nhan(ket_qua, 0, quan_the, fitness, 0, 0)

        for the_he in range(1, cfg.so_the_he + 1):
            if self.stop_event is not None and self.stop_event.is_set():
                ket_qua.bi_dung = True
                break
            quan_the, so_lai, so_dot_bien = self._the_he_ke_tiep(quan_the, fitness)
            fitness = self._danh_gia(quan_the)
            self._ghi_nhan(ket_qua, the_he, quan_the, fitness, so_lai, so_dot_bien)
            ket_qua.so_the_he_da_chay = the_he

        ket_qua.thoi_gian_chay = time.perf_counter() - bat_dau
        return ket_qua

    def _danh_gia(self, quan_the: op.QuanThe) -> list[float]:
        """Tính fitness cho toàn bộ quần thể."""
        return [op.tinh_fitness(c, self.ma_tran) for c in quan_the]

    def _chon_cha_me(self, quan_the: op.QuanThe, fitness: list[float]) -> op.CaThe:
        """Chọn một cá thể làm cha/mẹ theo phương pháp trong cấu hình."""
        if self.cau_hinh.phuong_phap_chon == CHON_LOC_ROULETTE:
            return op.chon_loc_roulette(quan_the, fitness, self.rng)
        return op.chon_loc_giai_dau(quan_the, fitness, self.rng, self.cau_hinh.kich_thuoc_giai)

    def _dot_bien(self, ca_the: op.CaThe) -> op.CaThe:
        """Đột biến một cá thể theo phương pháp trong cấu hình."""
        if self.cau_hinh.phuong_phap_dot_bien == DOT_BIEN_SWAP:
            return op.dot_bien_swap(ca_the, self.rng)
        return op.dot_bien_inversion(ca_the, self.rng)

    def _the_he_ke_tiep(
        self, quan_the: op.QuanThe, fitness: list[float]
    ) -> tuple[op.QuanThe, int, int]:
        """Sinh quần thể thế hệ kế tiếp.

        Trả về:
            (quần thể mới, số cặp đã lai ghép, số cá thể con bị đột biến).
        """
        cfg = self.cau_hinh
        moi = op.chon_elite(quan_the, fitness, cfg.so_elite)
        so_lai = so_dot_bien = 0

        while len(moi) < cfg.so_ca_the:
            cha = self._chon_cha_me(quan_the, fitness)
            me = self._chon_cha_me(quan_the, fitness)
            if self.rng.random() < cfg.ty_le_lai_ghep:
                con1, con2 = op.lai_ghep_ox(cha, me, self.rng)
                so_lai += 1
            else:
                con1, con2 = cha, me
            for con in (con1, con2):
                if len(moi) >= cfg.so_ca_the:
                    break
                if self.rng.random() < cfg.ty_le_dot_bien:
                    con = self._dot_bien(con)
                    so_dot_bien += 1
                moi.append(con)
        return moi, so_lai, so_dot_bien

    def _ghi_nhan(
        self,
        ket_qua: GAResult,
        the_he: int,
        quan_the: op.QuanThe,
        fitness: list[float],
        so_lai: int,
        so_dot_bien: int,
    ) -> None:
        """Cập nhật kết quả, lịch sử hội tụ và gọi callback cho giao diện."""
        chi_so_tot = max(range(len(fitness)), key=lambda i: fitness[i])
        tuyen = quan_the[chi_so_tot][:]
        tot_nhat = tinh_tong_quang_duong(tuyen, self.ma_tran)
        trung_binh = float(np.mean([1.0 / f for f in fitness]))

        cai_thien = tot_nhat < ket_qua.quang_duong_tot_nhat
        if cai_thien:
            ket_qua.tuyen_tot_nhat = tuyen
            ket_qua.quang_duong_tot_nhat = tot_nhat
        ket_qua.lich_su_tot_nhat.append(tot_nhat)
        ket_qua.lich_su_trung_binh.append(trung_binh)

        if self.on_generation is not None:
            self.on_generation(
                ThongKeTheHe(
                    the_he=the_he,
                    tot_nhat=tot_nhat,
                    trung_binh=trung_binh,
                    tuyen_tot_nhat=tuyen,
                    so_lai_ghep=so_lai,
                    so_dot_bien=so_dot_bien,
                    cai_thien=cai_thien,
                )
            )

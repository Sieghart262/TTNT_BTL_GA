"""Các toán tử của Giải thuật di truyền (GA) cho bài toán TSP.

Mỗi cá thể (nhiễm sắc thể) là một hoán vị các chỉ số địa điểm, ví dụ
[3, 0, 14, ...]. Mọi toán tử đều đảm bảo kết quả vẫn là hoán vị hợp lệ
(mỗi địa điểm xuất hiện đúng 1 lần).

Các hàm ngẫu nhiên nhận tham số `rng` (random.Random) để có thể tái lập
kết quả bằng seed.
"""

from __future__ import annotations

import random
from typing import Sequence

import numpy as np

from ga.data import tinh_tong_quang_duong

CaThe = list[int]
QuanThe = list[CaThe]


def tao_quan_the(so_ca_the: int, so_diem: int, rng: random.Random) -> QuanThe:
    """Khởi tạo quần thể gồm các hoán vị ngẫu nhiên.

    Tham số:
        so_ca_the: số cá thể trong quần thể.
        so_diem: số địa điểm (độ dài mỗi cá thể).
        rng: bộ sinh số ngẫu nhiên.

    Trả về:
        Danh sách `so_ca_the` hoán vị ngẫu nhiên của [0 .. so_diem-1].
    """
    quan_the = []
    for _ in range(so_ca_the):
        ca_the = list(range(so_diem))
        rng.shuffle(ca_the)
        quan_the.append(ca_the)
    return quan_the


def tinh_fitness(ca_the: Sequence[int], ma_tran: np.ndarray) -> float:
    """Tính độ thích nghi (fitness) của một cá thể.

    fitness = 1 / tổng quãng đường, nên quãng đường càng ngắn thì
    fitness càng lớn (bài toán cực đại hoá fitness).

    Tham số:
        ca_the: hoán vị các địa điểm.
        ma_tran: ma trận khoảng cách (km).

    Trả về:
        Giá trị fitness (> 0).
    """
    return 1.0 / tinh_tong_quang_duong(ca_the, ma_tran)


def chon_loc_giai_dau(
    quan_the: QuanThe,
    fitness: Sequence[float],
    rng: random.Random,
    kich_thuoc_giai: int = 3,
) -> CaThe:
    """Chọn lọc kiểu giải đấu (Tournament Selection).

    Chọn ngẫu nhiên `kich_thuoc_giai` cá thể rồi lấy cá thể có fitness cao
    nhất. Giải đấu càng lớn thì áp lực chọn lọc càng mạnh.

    Tham số:
        quan_the: quần thể hiện tại.
        fitness: fitness tương ứng của từng cá thể (cùng thứ tự với quan_the).
        rng: bộ sinh số ngẫu nhiên.
        kich_thuoc_giai: số cá thể tham gia mỗi giải đấu.

    Trả về:
        Bản sao của cá thể thắng cuộc.
    """
    k = min(kich_thuoc_giai, len(quan_the))
    ung_vien = rng.sample(range(len(quan_the)), k)
    thang = max(ung_vien, key=lambda i: fitness[i])
    return quan_the[thang][:]


def chon_loc_roulette(
    quan_the: QuanThe,
    fitness: Sequence[float],
    rng: random.Random,
) -> CaThe:
    """Chọn lọc bánh xe quay (Roulette Wheel Selection).

    Xác suất được chọn tỷ lệ thuận với fitness của cá thể.

    Tham số:
        quan_the: quần thể hiện tại.
        fitness: fitness tương ứng của từng cá thể.
        rng: bộ sinh số ngẫu nhiên.

    Trả về:
        Bản sao của cá thể được chọn.
    """
    chi_so = rng.choices(range(len(quan_the)), weights=fitness, k=1)[0]
    return quan_the[chi_so][:]


def lai_ghep_ox(cha: Sequence[int], me: Sequence[int], rng: random.Random) -> tuple[CaThe, CaThe]:
    """Lai ghép thứ tự (Order Crossover - OX).

    Các bước (với mỗi con):
        1. Chọn ngẫu nhiên đoạn [a, b] và sao chép nguyên đoạn đó từ cha sang con.
        2. Điền các vị trí còn lại bằng các gen của mẹ theo thứ tự xuất hiện
           (bắt đầu sau vị trí b, quay vòng), bỏ qua gen đã có trong đoạn.
    Nhờ vậy con luôn là hoán vị hợp lệ và giữ được thứ tự tương đối của mẹ.

    Tham số:
        cha, me: hai cá thể bố mẹ (cùng độ dài).
        rng: bộ sinh số ngẫu nhiên.

    Trả về:
        Tuple gồm hai cá thể con.
    """
    n = len(cha)
    a, b = sorted(rng.sample(range(n), 2))
    return _ox_mot_con(cha, me, a, b), _ox_mot_con(me, cha, a, b)


def _ox_mot_con(cha: Sequence[int], me: Sequence[int], a: int, b: int) -> CaThe:
    """Sinh một con theo OX: giữ đoạn [a, b] của `cha`, phần còn lại lấy từ `me`."""
    n = len(cha)
    con: list[int | None] = [None] * n
    con[a : b + 1] = cha[a : b + 1]
    da_co = set(cha[a : b + 1])
    # Duyệt gen của mẹ bắt đầu từ sau vị trí b (quay vòng) và điền vào các ô trống.
    vi_tri_dien = (b + 1) % n
    for k in range(n):
        gen = me[(b + 1 + k) % n]
        if gen in da_co:
            continue
        con[vi_tri_dien] = gen
        vi_tri_dien = (vi_tri_dien + 1) % n
    return con  # type: ignore[return-value]


def dot_bien_swap(ca_the: Sequence[int], rng: random.Random) -> CaThe:
    """Đột biến hoán đổi (Swap Mutation): đổi chỗ hai địa điểm ngẫu nhiên.

    Tham số:
        ca_the: cá thể gốc (không bị thay đổi).
        rng: bộ sinh số ngẫu nhiên.

    Trả về:
        Cá thể mới sau đột biến.
    """
    moi = list(ca_the)
    i, j = rng.sample(range(len(moi)), 2)
    moi[i], moi[j] = moi[j], moi[i]
    return moi


def dot_bien_inversion(ca_the: Sequence[int], rng: random.Random) -> CaThe:
    """Đột biến đảo đoạn (Inversion Mutation): đảo ngược một đoạn con ngẫu nhiên.

    Với TSP, phép này gỡ được các cạnh giao nhau nên hiệu quả hơn Swap.

    Tham số:
        ca_the: cá thể gốc (không bị thay đổi).
        rng: bộ sinh số ngẫu nhiên.

    Trả về:
        Cá thể mới sau đột biến.
    """
    moi = list(ca_the)
    i, j = sorted(rng.sample(range(len(moi)), 2))
    moi[i : j + 1] = reversed(moi[i : j + 1])
    return moi


def chon_elite(quan_the: QuanThe, fitness: Sequence[float], so_elite: int) -> QuanThe:
    """Chọn `so_elite` cá thể tốt nhất để giữ nguyên sang thế hệ sau (Elitism).

    Tham số:
        quan_the: quần thể hiện tại.
        fitness: fitness tương ứng.
        so_elite: số cá thể ưu tú cần giữ.

    Trả về:
        Danh sách bản sao các cá thể ưu tú, xếp theo fitness giảm dần.
    """
    chi_so = sorted(range(len(quan_the)), key=lambda i: fitness[i], reverse=True)[:so_elite]
    return [quan_the[i][:] for i in chi_so]

"""Các thuật toán đối chứng để đánh giá chất lượng lời giải của GA.

    - Held-Karp (quy hoạch động): cho nghiệm TỐI ƯU, chỉ dùng được khi số điểm
      nhỏ (độ phức tạp O(n^2 * 2^n), thực tế n <= 18).
    - Nearest Neighbor (láng giềng gần nhất): heuristic tham lam, nhanh, dùng
      làm mốc so sánh khi số điểm lớn.

Module không phụ thuộc giao diện.
"""

from __future__ import annotations

import numpy as np

from ga.data import tinh_tong_quang_duong

SO_DIEM_TOI_DA_HELD_KARP = 18


def held_karp(ma_tran: np.ndarray) -> tuple[float, list[int]]:
    """Tìm chu trình ngắn nhất chính xác bằng quy hoạch động Held-Karp.

    dp[tap][j] = quãng đường ngắn nhất xuất phát từ điểm 0, đi qua đúng các
    điểm trong `tap` (bitmask) và kết thúc tại j.

    Tham số:
        ma_tran: ma trận khoảng cách (n, n), n <= 18.

    Trả về:
        (độ dài tối ưu, tuyến tối ưu bắt đầu từ điểm 0).

    Ngoại lệ:
        ValueError nếu n quá lớn hoặc quá nhỏ.
    """
    n = ma_tran.shape[0]
    if n < 3:
        raise ValueError("Cần ít nhất 3 điểm.")
    if n > SO_DIEM_TOI_DA_HELD_KARP:
        raise ValueError(f"Held-Karp chỉ hỗ trợ tối đa {SO_DIEM_TOI_DA_HELD_KARP} điểm.")

    vo_cung = float("inf")
    dp = np.full((1 << n, n), vo_cung)
    cha = np.full((1 << n, n), -1, dtype=int)
    dp[1][0] = 0.0
    for tap in range(1, 1 << n):
        if not tap & 1:
            continue
        for j in range(n):
            if dp[tap][j] == vo_cung:
                continue
            for k in range(1, n):
                if tap >> k & 1:
                    continue
                moi = tap | (1 << k)
                gia_tri = dp[tap][j] + ma_tran[j][k]
                if gia_tri < dp[moi][k]:
                    dp[moi][k] = gia_tri
                    cha[moi][k] = j

    day_du = (1 << n) - 1
    cuoi = min(range(1, n), key=lambda j: dp[day_du][j] + ma_tran[j][0])
    toi_uu = float(dp[day_du][cuoi] + ma_tran[cuoi][0])

    # Truy vết ngược để dựng lại tuyến
    tuyen, tap, j = [], day_du, cuoi
    while j != -1:
        tuyen.append(j)
        tap, j = tap ^ (1 << j), int(cha[tap][j])
    return toi_uu, tuyen[::-1]


def lang_gieng_gan_nhat(ma_tran: np.ndarray, diem_dau: int = 0) -> tuple[float, list[int]]:
    """Heuristic láng giềng gần nhất: luôn đi tiếp tới điểm chưa thăm gần nhất.

    Tham số:
        ma_tran: ma trận khoảng cách (n, n).
        diem_dau: điểm xuất phát.

    Trả về:
        (độ dài chu trình, tuyến).
    """
    n = ma_tran.shape[0]
    tuyen = [diem_dau]
    chua_tham = set(range(n)) - {diem_dau}
    while chua_tham:
        tiep = min(chua_tham, key=lambda j: ma_tran[tuyen[-1]][j])
        tuyen.append(tiep)
        chua_tham.remove(tiep)
    return tinh_tong_quang_duong(tuyen, ma_tran), tuyen

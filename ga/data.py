"""Dữ liệu bài toán người chào hàng (TSP) với 15 địa danh ở Hà Nội.

Module này chỉ chứa dữ liệu và các hàm tính khoảng cách; không phụ thuộc
vào giao diện (tkinter) hay thư viện vẽ (matplotlib).

Lưu ý: toạ độ (vĩ độ, kinh độ) là giá trị gần đúng, cần đối chiếu lại
với Google Maps trước khi đưa vào báo cáo.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

# Bán kính trung bình của Trái Đất (km), dùng cho công thức Haversine.
BAN_KINH_TRAI_DAT_KM = 6371.0

# Danh sách 15 địa danh: (tên, vĩ độ, kinh độ).
DIA_DIEM: list[tuple[str, float, float]] = [
    ("Hồ Hoàn Kiếm", 21.0285, 105.8522),
    ("Lăng Bác", 21.0368, 105.8346),
    ("Văn Miếu - Quốc Tử Giám", 21.0275, 105.8355),
    ("Hồ Tây", 21.0583, 105.8230),
    ("Nhà hát Lớn", 21.0242, 105.8575),
    ("Bến xe Mỹ Đình", 21.0286, 105.7783),
    ("SVĐ Quốc gia Mỹ Đình", 21.0208, 105.7646),
    ("ĐH Bách khoa Hà Nội", 21.0045, 105.8433),
    ("ĐH Kinh tế Quốc dân", 21.0003, 105.8436),
    ("Ga Hà Nội", 21.0245, 105.8412),
    ("Royal City", 20.9996, 105.8150),
    ("Times City", 20.9951, 105.8686),
    ("Aeon Mall Long Biên", 21.0272, 105.8997),
    ("Cầu Long Biên", 21.0436, 105.8587),
    ("Công viên Thống Nhất", 21.0113, 105.8447),
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách đường tròn lớn giữa hai điểm trên Trái Đất.

    Dùng công thức Haversine, phù hợp với toạ độ địa lý (vĩ độ, kinh độ).

    Tham số:
        lat1, lon1: vĩ độ và kinh độ điểm thứ nhất (đơn vị độ).
        lat2, lon2: vĩ độ và kinh độ điểm thứ hai (đơn vị độ).

    Trả về:
        Khoảng cách giữa hai điểm, đơn vị km.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * BAN_KINH_TRAI_DAT_KM * math.asin(math.sqrt(a))


def lay_ten_dia_diem() -> list[str]:
    """Trả về danh sách tên các địa điểm theo đúng thứ tự chỉ số 0..N-1."""
    return [ten for ten, _, _ in DIA_DIEM]


def lay_toa_do() -> np.ndarray:
    """Trả về mảng toạ độ kích thước (N, 2); mỗi dòng là (vĩ độ, kinh độ)."""
    return np.array([(lat, lon) for _, lat, lon in DIA_DIEM], dtype=float)


def tao_ma_tran_khoang_cach(toa_do: np.ndarray | None = None) -> np.ndarray:
    """Tạo ma trận khoảng cách (km) giữa mọi cặp địa điểm.

    Tham số:
        toa_do: mảng (N, 2) gồm (vĩ độ, kinh độ). Mặc định dùng 15 địa danh Hà Nội.

    Trả về:
        Ma trận vuông (N, N) đối xứng, đường chéo bằng 0; phần tử [i][j] là
        khoảng cách từ địa điểm i đến địa điểm j.
    """
    if toa_do is None:
        toa_do = lay_toa_do()
    n = len(toa_do)
    ma_tran = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(toa_do[i][0], toa_do[i][1], toa_do[j][0], toa_do[j][1])
            ma_tran[i][j] = ma_tran[j][i] = d
    return ma_tran


def tinh_tong_quang_duong(tuyen: Sequence[int], ma_tran: np.ndarray) -> float:
    """Tính tổng độ dài của một chu trình khép kín.

    Chu trình đi qua các địa điểm theo thứ tự trong `tuyen` rồi quay về
    điểm xuất phát.

    Tham số:
        tuyen: hoán vị các chỉ số địa điểm.
        ma_tran: ma trận khoảng cách (N, N).

    Trả về:
        Tổng quãng đường (km).
    """
    n = len(tuyen)
    return float(sum(ma_tran[tuyen[i]][tuyen[(i + 1) % n]] for i in range(n)))

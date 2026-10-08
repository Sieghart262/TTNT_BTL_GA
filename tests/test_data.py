"""Kiểm thử module ga.data: Haversine, ma trận khoảng cách, tổng quãng đường."""

import numpy as np
import pytest

from ga.data import (
    DIA_DIEM,
    haversine,
    lay_ten_dia_diem,
    tao_ma_tran_khoang_cach,
    tinh_tong_quang_duong,
)


def test_so_luong_dia_diem():
    assert len(DIA_DIEM) == 15
    assert len(set(lay_ten_dia_diem())) == 15  # tên không trùng


def test_toa_do_nam_trong_ha_noi():
    for ten, lat, lon in DIA_DIEM:
        assert 20.9 < lat < 21.1, ten
        assert 105.7 < lon < 105.95, ten


def test_haversine_cung_diem_bang_0():
    assert haversine(21.0, 105.8, 21.0, 105.8) == 0


def test_haversine_1_do_vi_do():
    # 1 độ vĩ độ ≈ 111.19 km
    assert haversine(0, 0, 1, 0) == pytest.approx(111.19, abs=0.1)


def test_ma_tran_doi_xung_va_duong_cheo_0():
    m = tao_ma_tran_khoang_cach()
    assert m.shape == (15, 15)
    assert np.allclose(m, m.T)
    assert np.all(np.diag(m) == 0)
    assert np.all(m[~np.eye(15, dtype=bool)] > 0)


def test_khoang_cach_hop_ly():
    # Mọi cặp địa điểm trong nội thành Hà Nội cách nhau dưới 30 km
    assert tao_ma_tran_khoang_cach().max() < 30


def test_tong_quang_duong_khep_kin():
    # Hình vuông 3 điểm giả lập: 0-1-2 với khoảng cách 3,4,5 -> tổng 12
    m = np.array([[0, 3, 5], [3, 0, 4], [5, 4, 0]], dtype=float)
    assert tinh_tong_quang_duong([0, 1, 2], m) == 12


def test_tong_quang_duong_khong_phu_thuoc_diem_dau():
    m = tao_ma_tran_khoang_cach()
    tuyen = list(range(15))
    xoay = tuyen[5:] + tuyen[:5]
    assert tinh_tong_quang_duong(tuyen, m) == pytest.approx(tinh_tong_quang_duong(xoay, m))

"""Kiểm thử gui.plots: hai biểu đồ vẽ đúng nội dung và không lỗi với các trường hợp biên."""

import pytest
from matplotlib.figure import Figure

from ga.algorithm import GAConfig, GeneticAlgorithm
from ga.data import bai_toan_ha_noi, bai_toan_ngau_nhien
from gui.plots import ve_ban_do, ve_hoi_tu


def tao_truc():
    fig = Figure()
    return fig, fig.add_subplot(1, 1, 1)


def chay_ga(bai_toan, so_the_he=40):
    return GeneticAlgorithm(GAConfig(so_ca_the=40, so_the_he=so_the_he, seed=1), bai_toan.ma_tran).chay()


def test_hoi_tu_co_hai_duong_va_giam_dan():
    kq = chay_ga(bai_toan_ha_noi())
    _, ax = tao_truc()
    ve_hoi_tu(ax, kq.lich_su_tot_nhat, kq.lich_su_trung_binh, 40)
    tot = [l for l in ax.get_lines() if l.get_linewidth() == 2][0]
    assert list(tot.get_ydata()) == kq.lich_su_tot_nhat
    assert len(tot.get_xdata()) == 41
    assert ax.get_xlim() == (0, 40)
    assert {t.get_text() for t in ax.get_legend().get_texts()} == {"Trung bình quần thể", "Tốt nhất"}


def test_hoi_tu_rong_khong_loi():
    _, ax = tao_truc()
    ve_hoi_tu(ax, [], [])
    assert not ax.get_lines() and ax.texts


def test_hoi_tu_mot_phan_tu():
    _, ax = tao_truc()
    ve_hoi_tu(ax, [50.0], [55.0])


def test_ban_do_ve_tuyen_khep_kin():
    bt = bai_toan_ha_noi()
    kq = chay_ga(bt)
    _, ax = tao_truc()
    ve_ban_do(ax, bt, kq.tuyen_tot_nhat)
    # 15 mũi tên khép kín + 15 nhãn tên + 15 số thứ tự
    mui_ten = [a for a in ax.texts if getattr(a, "arrow_patch", None) is not None]
    assert len(mui_ten) == 15
    nhan = {a.get_text() for a in ax.texts if getattr(a, "arrow_patch", None) is None}
    assert {str(i) for i in range(1, 16)} <= nhan  # đủ số thứ tự
    # Tên được đặt không chồng nhau; phần bị ẩn (nếu có) phải được chú thích
    so_ten = len(nhan & set(bt.ten_dia_diem))
    assert so_ten >= 8
    if so_ten < 15:
        assert any("bị ẩn" in t for t in nhan)


def test_ban_do_chua_co_tuyen():
    _, ax = tao_truc()
    ve_ban_do(ax, bai_toan_ha_noi(), None)
    assert not [a for a in ax.texts if getattr(a, "arrow_patch", None) is not None]


def test_ban_do_nhieu_diem_dung_duong_thang_khong_nhan():
    bt = bai_toan_ngau_nhien(100, seed=1)
    kq = chay_ga(bt, 5)
    _, ax = tao_truc()
    ve_ban_do(ax, bt, kq.tuyen_tot_nhat)
    assert not ax.texts
    duong = [l for l in ax.get_lines() if len(l.get_xdata()) == 101]
    assert len(duong) == 1


def test_ban_do_tuyen_sai_do_dai_bi_bo_qua():
    _, ax = tao_truc()
    ve_ban_do(ax, bai_toan_ha_noi(), [0, 1, 2])
    assert not [a for a in ax.texts if getattr(a, "arrow_patch", None) is not None]

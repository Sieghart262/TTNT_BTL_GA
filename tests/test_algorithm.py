"""Kiểm thử module ga.algorithm: cấu hình, hội tụ, tái lập, dừng sớm, callback."""

import threading

import pytest

from ga.algorithm import GAConfig, GeneticAlgorithm
from ga.data import tao_ma_tran_khoang_cach, tinh_tong_quang_duong


@pytest.fixture(scope="module")
def ma_tran():
    return tao_ma_tran_khoang_cach()


def cau_hinh_nhanh(**kw):
    mac_dinh = dict(so_ca_the=60, so_the_he=80, seed=7)
    mac_dinh.update(kw)
    return GAConfig(**mac_dinh)


@pytest.mark.parametrize(
    "thay_doi",
    [
        dict(so_ca_the=1),
        dict(so_the_he=0),
        dict(ty_le_dot_bien=-0.1),
        dict(ty_le_dot_bien=1.5),
        dict(ty_le_lai_ghep=2),
        dict(so_elite=100, so_ca_the=50),
        dict(kich_thuoc_giai=0),
        dict(phuong_phap_chon="abc"),
        dict(phuong_phap_dot_bien="abc"),
    ],
)
def test_cau_hinh_khong_hop_le(thay_doi, ma_tran):
    with pytest.raises(ValueError):
        GeneticAlgorithm(cau_hinh_nhanh(**thay_doi), ma_tran)


def test_ket_qua_hop_le(ma_tran):
    kq = GeneticAlgorithm(cau_hinh_nhanh(), ma_tran).chay()
    assert sorted(kq.tuyen_tot_nhat) == list(range(15))
    assert kq.quang_duong_tot_nhat == pytest.approx(tinh_tong_quang_duong(kq.tuyen_tot_nhat, ma_tran))
    assert kq.so_the_he_da_chay == 80
    assert len(kq.lich_su_tot_nhat) == len(kq.lich_su_trung_binh) == 81  # gồm thế hệ 0
    assert not kq.bi_dung


def test_hoi_tu_khong_tang_nho_elitism(ma_tran):
    ls = GeneticAlgorithm(cau_hinh_nhanh(), ma_tran).chay().lich_su_tot_nhat
    assert all(b <= a + 1e-12 for a, b in zip(ls, ls[1:]))
    assert ls[-1] < ls[0]


@pytest.mark.parametrize("chon", ["tournament", "roulette"])
@pytest.mark.parametrize("dot_bien", ["inversion", "swap"])
def test_cac_phuong_phap_deu_cai_thien(ma_tran, chon, dot_bien):
    cfg = cau_hinh_nhanh(phuong_phap_chon=chon, phuong_phap_dot_bien=dot_bien)
    kq = GeneticAlgorithm(cfg, ma_tran).chay()
    assert kq.quang_duong_tot_nhat < kq.lich_su_tot_nhat[0]


def test_tai_lap_cung_seed(ma_tran):
    a = GeneticAlgorithm(cau_hinh_nhanh(), ma_tran).chay()
    b = GeneticAlgorithm(cau_hinh_nhanh(), ma_tran).chay()
    assert a.tuyen_tot_nhat == b.tuyen_tot_nhat
    assert a.lich_su_tot_nhat == b.lich_su_tot_nhat


def test_khac_seed_cho_khac_lich_su(ma_tran):
    a = GeneticAlgorithm(cau_hinh_nhanh(seed=1), ma_tran).chay()
    b = GeneticAlgorithm(cau_hinh_nhanh(seed=2), ma_tran).chay()
    assert a.lich_su_tot_nhat != b.lich_su_tot_nhat


def test_callback_goi_moi_the_he(ma_tran):
    nhan = []
    GeneticAlgorithm(cau_hinh_nhanh(so_the_he=20), ma_tran, on_generation=nhan.append).chay()
    assert [t.the_he for t in nhan] == list(range(21))
    assert nhan[0].cai_thien  # thế hệ 0 luôn là kỷ lục đầu tiên
    assert all(sorted(t.tuyen_tot_nhat) == list(range(15)) for t in nhan)
    assert sum(t.so_lai_ghep for t in nhan) > 0


def test_ty_le_bang_0_khong_lai_khong_dot_bien(ma_tran):
    nhan = []
    cfg = cau_hinh_nhanh(so_the_he=10, ty_le_lai_ghep=0, ty_le_dot_bien=0)
    GeneticAlgorithm(cfg, ma_tran, on_generation=nhan.append).chay()
    assert sum(t.so_lai_ghep + t.so_dot_bien for t in nhan) == 0


def test_dung_som_bang_stop_event(ma_tran):
    stop = threading.Event()

    def khi_den_the_he_5(tk):
        if tk.the_he == 5:
            stop.set()

    kq = GeneticAlgorithm(
        cau_hinh_nhanh(so_the_he=1000), ma_tran, on_generation=khi_den_the_he_5, stop_event=stop
    ).chay()
    assert kq.bi_dung
    assert kq.so_the_he_da_chay == 5
    assert sorted(kq.tuyen_tot_nhat) == list(range(15))


def test_chay_trong_thread_nen(ma_tran):
    kq = []
    t = threading.Thread(target=lambda: kq.append(GeneticAlgorithm(cau_hinh_nhanh(), ma_tran).chay()))
    t.start()
    t.join(timeout=30)
    assert not t.is_alive() and len(kq) == 1


def test_quan_the_le_van_du_so_ca_the(ma_tran):
    kq = GeneticAlgorithm(cau_hinh_nhanh(so_ca_the=7, so_the_he=10), ma_tran).chay()
    assert sorted(kq.tuyen_tot_nhat) == list(range(15))

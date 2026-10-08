"""Kiểm thử module ga.operators: mọi toán tử phải sinh ra hoán vị hợp lệ."""

import random

import pytest

from ga.data import tao_ma_tran_khoang_cach
from ga.operators import (
    chon_elite,
    chon_loc_giai_dau,
    chon_loc_roulette,
    dot_bien_inversion,
    dot_bien_swap,
    lai_ghep_ox,
    tao_quan_the,
    tinh_fitness,
)

N = 15
LAP = 500  # số lần lặp cho các kiểm thử ngẫu nhiên


def hop_le(ca_the, n=N):
    return sorted(ca_the) == list(range(n))


@pytest.fixture
def rng():
    return random.Random(42)


def test_tao_quan_the(rng):
    qt = tao_quan_the(50, N, rng)
    assert len(qt) == 50
    assert all(hop_le(c) for c in qt)
    assert len({tuple(c) for c in qt}) > 1  # không phải toàn cá thể giống nhau


def test_tinh_fitness_nghich_dao_quang_duong():
    m = tao_ma_tran_khoang_cach()
    ca_the = list(range(N))
    from ga.data import tinh_tong_quang_duong

    assert tinh_fitness(ca_the, m) == pytest.approx(1 / tinh_tong_quang_duong(ca_the, m))


def test_lai_ghep_ox_sinh_hoan_vi_hop_le(rng):
    for _ in range(LAP):
        cha, me = tao_quan_the(2, N, rng)
        con1, con2 = lai_ghep_ox(cha, me, rng)
        assert hop_le(con1) and hop_le(con2)


def test_lai_ghep_ox_khong_sua_bo_me(rng):
    cha, me = tao_quan_the(2, N, rng)
    cha0, me0 = cha[:], me[:]
    lai_ghep_ox(cha, me, rng)
    assert cha == cha0 and me == me0


def test_lai_ghep_ox_giu_doan_cua_cha():
    # Cố định đoạn [2, 4] bằng cách giả lập rng
    class RngCoDinh(random.Random):
        def sample(self, population, k):
            return [2, 4]

    cha = [0, 1, 2, 3, 4, 5, 6, 7]
    me = [7, 6, 5, 4, 3, 2, 1, 0]
    con1, con2 = lai_ghep_ox(cha, me, RngCoDinh())
    assert con1[2:5] == [2, 3, 4]
    assert con2[2:5] == [5, 4, 3]
    assert hop_le(con1, 8) and hop_le(con2, 8)


def test_dot_bien_swap(rng):
    for _ in range(LAP):
        goc = tao_quan_the(1, N, rng)[0]
        moi = dot_bien_swap(goc, rng)
        assert hop_le(moi)
        assert sum(a != b for a, b in zip(goc, moi)) == 2  # đúng 2 vị trí thay đổi


def test_dot_bien_inversion(rng):
    for _ in range(LAP):
        goc = tao_quan_the(1, N, rng)[0]
        goc0 = goc[:]
        moi = dot_bien_inversion(goc, rng)
        assert hop_le(moi)
        assert goc == goc0  # không sửa cá thể gốc


def test_chon_loc_giai_dau_chon_ca_the_tot_nhat_khi_giai_bang_quan_the(rng):
    qt = tao_quan_the(10, N, rng)
    fit = [float(i) for i in range(10)]  # cá thể cuối tốt nhất
    assert chon_loc_giai_dau(qt, fit, rng, kich_thuoc_giai=10) == qt[9]


def test_chon_loc_tra_ve_ban_sao(rng):
    qt = tao_quan_the(10, N, rng)
    fit = [1.0] * 10
    for ham in (
        lambda: chon_loc_giai_dau(qt, fit, rng),
        lambda: chon_loc_roulette(qt, fit, rng),
    ):
        chon = ham()
        assert hop_le(chon)
        assert all(chon is not c for c in qt)


def test_chon_loc_roulette_uu_tien_fitness_cao(rng):
    qt = tao_quan_the(2, N, rng)
    fit = [1e-9, 1.0]
    dem = sum(chon_loc_roulette(qt, fit, rng) == qt[1] for _ in range(200))
    assert dem > 190


def test_chon_elite(rng):
    qt = tao_quan_the(10, N, rng)
    fit = [3, 9, 1, 7, 5, 2, 8, 4, 6, 0]
    elite = chon_elite(qt, fit, 2)
    assert elite == [qt[1], qt[6]]
    assert elite[0] is not qt[1]

"""Kiểm thử ga.baseline: Held-Karp phải khớp vét cạn, láng giềng gần nhất hợp lệ."""

import itertools

import numpy as np
import pytest

from ga.baseline import held_karp, lang_gieng_gan_nhat
from ga.data import bai_toan_ngau_nhien, tinh_tong_quang_duong


def vet_can(ma_tran):
    n = len(ma_tran)
    return min(tinh_tong_quang_duong([0, *p], ma_tran) for p in itertools.permutations(range(1, n)))


@pytest.mark.parametrize("n,seed", [(4, 1), (6, 2), (8, 3)])
def test_held_karp_khop_vet_can(n, seed):
    m = bai_toan_ngau_nhien(n, seed).ma_tran
    do_dai, tuyen = held_karp(m)
    assert do_dai == pytest.approx(vet_can(m))
    assert sorted(tuyen) == list(range(n)) and tuyen[0] == 0
    assert tinh_tong_quang_duong(tuyen, m) == pytest.approx(do_dai)


def test_held_karp_tu_choi_dau_vao_sai():
    with pytest.raises(ValueError):
        held_karp(np.zeros((2, 2)))
    with pytest.raises(ValueError):
        held_karp(np.zeros((25, 25)))


def test_lang_gieng_gan_nhat_hop_le_va_khong_tot_hon_toi_uu():
    m = bai_toan_ngau_nhien(9, 5).ma_tran
    do_dai, tuyen = lang_gieng_gan_nhat(m)
    assert sorted(tuyen) == list(range(9))
    assert do_dai >= held_karp(m)[0] - 1e-9

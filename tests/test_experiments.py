"""Kiểm thử nhanh script thí nghiệm: thống kê, CSV và Markdown."""

import csv

from experiments import bang_markdown, chay_cau_hinh, ghi_csv
from ga.algorithm import GAConfig
from ga.baseline import held_karp
from ga.data import bai_toan_ngau_nhien


def test_chay_cau_hinh_va_xuat_bao_cao(tmp_path):
    bt = bai_toan_ngau_nhien(8, seed=1)
    toi_uu, _ = held_karp(bt.ma_tran)
    d = chay_cau_hinh("A. Thử", "x", GAConfig(so_ca_the=30, so_the_he=40), bt, 3, toi_uu, True)
    assert d.so_seed == 3 and d.tot_nhat >= toi_uu - 1e-9
    assert d.sai_so_pct >= -1e-6 and 0 <= d.so_lan_toi_uu <= 3
    assert 0 <= d.the_he_hoi_tu <= 40

    ghi_csv(tmp_path / "kq.csv", [d])
    dong = list(csv.reader(open(tmp_path / "kq.csv", encoding="utf-8-sig")))
    assert len(dong) == 2 and dong[1][0] == "A. Thử"

    md = bang_markdown([d], toi_uu, [(d, 10.0, 8)])
    assert "## A. Thử" in md and "## E. Quy mô bài toán" in md

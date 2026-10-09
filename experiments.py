"""Chạy thí nghiệm GA với nhiều bộ tham số để lấy số liệu cho báo cáo.

Mỗi cấu hình được chạy với nhiều seed rồi thống kê. Kết quả ghi ra:
    docs/ket_qua_thi_nghiem.csv  - số liệu thô theo từng cấu hình
    docs/ket_qua_thi_nghiem.md   - bảng Markdown, dán thẳng vào báo cáo

Cách chạy:
    python experiments.py                 # đầy đủ (20 seed mỗi cấu hình, khoảng 2 phút)
    python experiments.py --nhanh         # bản rút gọn (3 seed) để thử
    python experiments.py --so-seed 50    # tuỳ chỉnh số seed

Module chỉ dùng gói ga/, không phụ thuộc giao diện.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from dataclasses import dataclass, replace
from pathlib import Path

from ga.algorithm import GAConfig, GeneticAlgorithm
from ga.baseline import held_karp, lang_gieng_gan_nhat
from ga.data import BaiToan, bai_toan_ha_noi, bai_toan_ngau_nhien

THU_MUC_KET_QUA = Path("docs")
SAI_SO_TOI_UU = 1e-6  # km, ngưỡng coi là "đạt tối ưu"


@dataclass
class DongKetQua:
    """Thống kê của một cấu hình chạy qua nhiều seed.

    Thuộc tính:
        nhom: tên nhóm thí nghiệm (ví dụ "Số cá thể").
        nhan: nhãn giá trị tham số của cấu hình (ví dụ "50").
        tb: quãng đường tốt nhất trung bình qua các seed (km).
        do_lech: độ lệch chuẩn qua các seed (km).
        tot_nhat: quãng đường tốt nhất trong mọi seed (km).
        sai_so_pct: sai số trung bình so với mốc tham chiếu (%).
        so_lan_toi_uu: số seed đạt nghiệm tối ưu (None nếu không biết nghiệm tối ưu).
        the_he_hoi_tu: thế hệ trung bình mà kỷ lục cuối cùng xuất hiện.
        thoi_gian: thời gian chạy trung bình mỗi lần (giây).
        so_seed: số seed đã chạy.
    """

    nhom: str
    nhan: str
    tb: float
    do_lech: float
    tot_nhat: float
    sai_so_pct: float
    so_lan_toi_uu: int | None
    the_he_hoi_tu: float
    thoi_gian: float
    so_seed: int


def chay_cau_hinh(
    nhom: str,
    nhan: str,
    cau_hinh: GAConfig,
    bai_toan: BaiToan,
    so_seed: int,
    moc: float,
    biet_toi_uu: bool,
) -> DongKetQua:
    """Chạy một cấu hình với seed 0..so_seed-1 và thống kê kết quả.

    Tham số:
        nhom, nhan: nhãn dùng khi ghi báo cáo.
        cau_hinh: cấu hình GA (seed sẽ bị ghi đè bởi từng seed).
        bai_toan: bài toán TSP.
        so_seed: số lần chạy độc lập.
        moc: quãng đường tham chiếu (tối ưu hoặc heuristic) để tính sai số.
        biet_toi_uu: True nếu `moc` là nghiệm tối ưu thật.

    Trả về:
        DongKetQua đã thống kê.
    """
    ket_qua = []
    for seed in range(so_seed):
        ga = GeneticAlgorithm(replace(cau_hinh, seed=seed), bai_toan.ma_tran)
        ket_qua.append(ga.chay())
    do_dai = [k.quang_duong_tot_nhat for k in ket_qua]
    the_he = [
        next(i for i, v in enumerate(k.lich_su_tot_nhat) if v <= k.quang_duong_tot_nhat + 1e-12)
        for k in ket_qua
    ]
    return DongKetQua(
        nhom=nhom,
        nhan=nhan,
        tb=statistics.fmean(do_dai),
        do_lech=statistics.pstdev(do_dai),
        tot_nhat=min(do_dai),
        sai_so_pct=(statistics.fmean(do_dai) / moc - 1) * 100,
        so_lan_toi_uu=sum(d <= moc + SAI_SO_TOI_UU for d in do_dai) if biet_toi_uu else None,
        the_he_hoi_tu=statistics.fmean(the_he),
        thoi_gian=statistics.fmean(k.thoi_gian_chay for k in ket_qua),
        so_seed=so_seed,
    )


def thi_nghiem_tham_so(so_seed: int) -> tuple[list[DongKetQua], float]:
    """Nhóm A-D: khảo sát tham số GA trên bài toán 15 điểm Hà Nội.

    Dùng cấu hình cơ sở "yếu" hơn mặc định (50 cá thể, 150 thế hệ) để sự khác
    biệt giữa các tham số lộ rõ; với tham số mặc định GA gần như luôn đạt tối ưu.

    Trả về:
        (danh sách kết quả, nghiệm tối ưu Held-Karp của bài toán).
    """
    bai_toan = bai_toan_ha_noi()
    toi_uu, _ = held_karp(bai_toan.ma_tran)
    co_so = GAConfig(so_ca_the=50, so_the_he=150, ty_le_dot_bien=0.05, ty_le_lai_ghep=0.85)
    dong: list[DongKetQua] = []

    def them(nhom: str, nhan: str, cau_hinh: GAConfig) -> None:
        """Chạy một cấu hình và thêm kết quả vào danh sách `dong`."""
        print(f"  [{nhom}] {nhan} ...", flush=True)
        dong.append(chay_cau_hinh(nhom, nhan, cau_hinh, bai_toan, so_seed, toi_uu, True))

    for n in (10, 20, 50, 100, 200):
        them("A. Số cá thể", str(n), replace(co_so, so_ca_the=n))
    for r in (0.0, 0.01, 0.05, 0.1, 0.3):
        them("B. Tỷ lệ đột biến", str(r), replace(co_so, ty_le_dot_bien=r))
    for r in (0.0, 0.3, 0.6, 0.85, 1.0):
        them("C. Tỷ lệ lai ghép", str(r), replace(co_so, ty_le_lai_ghep=r))
    for chon in ("tournament", "roulette"):
        for dot_bien in ("inversion", "swap"):
            them("D. Toán tử", f"{chon} + {dot_bien}", replace(co_so, phuong_phap_chon=chon, phuong_phap_dot_bien=dot_bien))
    return dong, toi_uu


def thi_nghiem_quy_mo(so_seed: int) -> list[tuple[DongKetQua, float, int]]:
    """Nhóm E: độ co giãn khi tăng số điểm (điểm ngẫu nhiên trong khung Hà Nội).

    Không biết nghiệm tối ưu khi N lớn nên so sánh với heuristic láng giềng gần nhất.

    Trả về:
        Danh sách (kết quả, quãng đường láng giềng gần nhất, N).
    """
    cau_hinh = GAConfig(so_ca_the=100, so_the_he=500)
    ket_qua = []
    for n in (15, 30, 60, 100):
        bai_toan = bai_toan_ha_noi() if n == 15 else bai_toan_ngau_nhien(n, seed=2024)
        nn, _ = lang_gieng_gan_nhat(bai_toan.ma_tran)
        print(f"  [E. Quy mô] N={n} ...", flush=True)
        dong = chay_cau_hinh("E. Quy mô", f"N={n}", cau_hinh, bai_toan, so_seed, nn, False)
        ket_qua.append((dong, nn, n))
    return ket_qua


def ghi_csv(duong_dan: Path, dong: list[DongKetQua]) -> None:
    """Ghi toàn bộ kết quả ra file CSV (UTF-8 có BOM để Excel đọc đúng tiếng Việt)."""
    cot = [
        "nhom", "nhan", "tb_km", "do_lech_km", "tot_nhat_km", "sai_so_pct",
        "so_lan_toi_uu", "the_he_hoi_tu", "thoi_gian_s", "so_seed",
    ]
    with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cot)
        for d in dong:
            w.writerow([
                d.nhom, d.nhan, f"{d.tb:.4f}", f"{d.do_lech:.4f}", f"{d.tot_nhat:.4f}",
                f"{d.sai_so_pct:.3f}", "" if d.so_lan_toi_uu is None else d.so_lan_toi_uu,
                f"{d.the_he_hoi_tu:.1f}", f"{d.thoi_gian:.3f}", d.so_seed,
            ])


def bang_markdown(dong: list[DongKetQua], toi_uu: float, quy_mo: list[tuple[DongKetQua, float, int]]) -> str:
    """Dựng nội dung Markdown gồm các bảng kết quả theo từng nhóm thí nghiệm.

    Tham số:
        dong: kết quả nhóm A-D.
        toi_uu: nghiệm tối ưu của bài toán 15 điểm.
        quy_mo: kết quả nhóm E.
    """
    so_seed = dong[0].so_seed
    out = [
        "# Kết quả thí nghiệm GA - TSP 15 địa danh Hà Nội\n",
        f"- Nghiệm tối ưu (Held-Karp): **{toi_uu:.3f} km**",
        "- Cấu hình cơ sở nhóm A-D: 50 cá thể, 150 thế hệ, đột biến 0.05 (inversion), lai ghép 0.85 (OX), "
        "chọn lọc tournament, elite 2",
        f"- Mỗi dòng là thống kê qua **{so_seed} seed** độc lập (seed 0..{so_seed - 1}).\n",
    ]
    nhom_hien_tai = None
    for d in dong:
        if d.nhom != nhom_hien_tai:
            nhom_hien_tai = d.nhom
            out += [
                f"\n## {d.nhom}\n",
                "| Giá trị | TB (km) | Độ lệch | Tốt nhất (km) | Sai số TB | Số lần tối ưu | Thế hệ hội tụ TB | Thời gian (s) |",
                "|---|---|---|---|---|---|---|---|",
            ]
        out.append(
            f"| {d.nhan} | {d.tb:.3f} | {d.do_lech:.3f} | {d.tot_nhat:.3f} | {d.sai_so_pct:.2f}% | "
            f"{d.so_lan_toi_uu}/{d.so_seed} | {d.the_he_hoi_tu:.0f} | {d.thoi_gian:.2f} |"
        )
    out += [
        "\n## E. Quy mô bài toán\n",
        "Cấu hình: 100 cá thể, 500 thế hệ. N=15 là 15 địa danh thật; N>15 là điểm ngẫu nhiên trong khung nội thành Hà Nội. "
        "Mốc so sánh là heuristic láng giềng gần nhất (NN). Giá trị âm nghĩa là GA với cấu hình này còn KÉM hơn NN "
        "(cần thêm cá thể/thế hệ hoặc cải tiến như khởi tạo bằng NN, tìm kiếm cục bộ 2-opt).\n",
        "| N | NN (km) | GA TB (km) | GA tốt nhất (km) | GA so với NN (dương = GA ngắn hơn) | Thế hệ hội tụ TB | Thời gian (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    for d, nn, n in quy_mo:
        out.append(
            f"| {n} | {nn:.3f} | {d.tb:.3f} | {d.tot_nhat:.3f} | {(1 - d.tb / nn) * 100:.1f}% | "
            f"{d.the_he_hoi_tu:.0f} | {d.thoi_gian:.2f} |"
        )
    return "\n".join(out) + "\n"


def main() -> None:
    """Chạy toàn bộ thí nghiệm và ghi file kết quả."""
    parser = argparse.ArgumentParser(description="Thí nghiệm GA cho TSP Hà Nội")
    parser.add_argument("--nhanh", action="store_true", help="chỉ chạy 3 seed mỗi cấu hình")
    parser.add_argument("--so-seed", type=int, default=20, help="số seed mỗi cấu hình (mặc định 20)")
    args = parser.parse_args()
    so_seed = 3 if args.nhanh else max(1, args.so_seed)

    bat_dau = time.perf_counter()
    print(f"Thí nghiệm tham số (A-D), {so_seed} seed/cấu hình:")
    dong, toi_uu = thi_nghiem_tham_so(so_seed)
    print(f"Thí nghiệm quy mô (E), {so_seed} seed/cấu hình:")
    quy_mo = thi_nghiem_quy_mo(so_seed)

    THU_MUC_KET_QUA.mkdir(exist_ok=True)
    ghi_csv(THU_MUC_KET_QUA / "ket_qua_thi_nghiem.csv", dong + [d for d, _, _ in quy_mo])
    (THU_MUC_KET_QUA / "ket_qua_thi_nghiem.md").write_text(bang_markdown(dong, toi_uu, quy_mo), encoding="utf-8")
    print(f"Xong sau {time.perf_counter() - bat_dau:.1f} giây. Đã ghi vào thư mục {THU_MUC_KET_QUA}/")


if __name__ == "__main__":
    main()

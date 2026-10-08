"""Kiểm thử lớp giao diện: worker (luồng nền), hàm kiểm tra nhập và chạy thử UI thật."""

import queue
import time
import tkinter as tk

import pytest

from ga.algorithm import GAConfig
from ga.data import bai_toan_ha_noi
from gui import worker as wk
from gui.app import UngDungGA, doc_seed, doc_so_nguyen, doc_so_thuc
from gui.worker import GAWorker


# ----------------------------------------------------------------- hàm kiểm tra nhập
def test_doc_so_nguyen():
    assert doc_so_nguyen(" 50 ", "x", 1) == 50
    for xau in ("abc", "", "1.5", "0"):
        with pytest.raises(ValueError):
            doc_so_nguyen(xau, "x", 1)
    with pytest.raises(ValueError):
        doc_so_nguyen("11", "x", 1, 10)


def test_doc_so_thuc_chap_nhan_dau_phay():
    assert doc_so_thuc("0,25", "x", 0, 1) == 0.25
    for xau in ("abc", "1.5", "-0.1", "nan", "inf"):
        with pytest.raises(ValueError):
            doc_so_thuc(xau, "x", 0, 1)


def test_doc_seed():
    assert doc_seed("") is None
    assert doc_seed(" 42 ") == 42
    with pytest.raises(ValueError):
        doc_seed("abc")


# ----------------------------------------------------------------- worker
def lay_het(w, timeout=20):
    """Chờ worker kết thúc và gom toàn bộ thông điệp."""
    msgs = []
    han = time.time() + timeout
    while time.time() < han:
        try:
            m = w.hang_doi.get(timeout=0.1)
        except queue.Empty:
            continue
        msgs.append(m)
        if m[0] in (wk.XONG, wk.LOI):
            return msgs
    raise AssertionError("worker không kết thúc đúng hạn")


def test_worker_gui_thong_diep():
    w = GAWorker(GAConfig(so_ca_the=30, so_the_he=15, seed=1), bai_toan_ha_noi())
    w.bat_dau()
    msgs = lay_het(w)
    loai = [m[0] for m in msgs]
    assert loai.count(wk.THE_HE) == 16 and loai[-1] == wk.XONG


def test_worker_dung_ngay_khi_dang_cho_do_tre():
    w = GAWorker(GAConfig(so_ca_the=30, so_the_he=1000, seed=1), bai_toan_ha_noi(), do_tre_ms=2000)
    w.bat_dau()
    time.sleep(0.3)
    t0 = time.time()
    w.dung()
    msgs = lay_het(w, timeout=5)
    assert time.time() - t0 < 1.5  # không phải chờ hết 2 giây độ trễ
    assert msgs[-1][1].bi_dung


def test_worker_bao_loi_qua_queue():
    w = GAWorker(GAConfig(so_ca_the=1), bai_toan_ha_noi())  # cấu hình sai
    w.bat_dau()
    assert lay_het(w)[-1][0] == wk.LOI


# ----------------------------------------------------------------- UI thật
@pytest.fixture
def ung_dung(monkeypatch):
    try:
        goc = tk.Tk()
    except tk.TclError:
        pytest.skip("Không có màn hình để chạy Tkinter")
    goc.withdraw()
    loi = []
    monkeypatch.setattr("gui.app.messagebox.showerror", lambda *a, **k: loi.append(a))
    app = UngDungGA(goc)
    app.loi_hien = loi
    yield app
    try:
        goc.destroy()
    except tk.TclError:
        pass


def bom_su_kien(app, dieu_kien, timeout=20):
    han = time.time() + timeout
    while time.time() < han:
        app.goc.update()
        if dieu_kien():
            return
        time.sleep(0.01)
    raise AssertionError("hết thời gian chờ giao diện")


def test_ui_chay_hoan_thanh_va_ghi_log(ung_dung):
    app = ung_dung
    app.v_so_ca_the.set("40")
    app.v_so_the_he.set("30")
    app.v_do_tre.set("0")
    app.v_seed.set("3")
    app.bat_dau_chay()
    assert str(app.nut_chay["state"]) == "disabled"
    bom_su_kien(app, lambda: app.ket_qua is not None and app.worker is None)

    log = app.o_log.get("1.0", "end")
    assert "BẮT ĐẦU" in log and "HOÀN THÀNH" in log and "Thế hệ 30/30" in log
    assert str(app.nut_chay["state"]) == "normal"
    assert app.ket_qua.so_the_he_da_chay == 30
    # Hai biểu đồ đã được vẽ với dữ liệu thật
    tot = [l for l in app.bieu_do.ax_hoi_tu.get_lines() if l.get_linewidth() == 2][0]
    assert list(tot.get_ydata()) == app.ket_qua.lich_su_tot_nhat
    assert len([a for a in app.bieu_do.ax_ban_do.texts if getattr(a, "arrow_patch", None) is not None]) == 15


def test_ui_khong_dung_khi_dang_cho_do_tre(ung_dung):
    """Giao diện vẫn xử lý sự kiện (update) được trong lúc GA đang chạy chậm."""
    app = ung_dung
    app.v_so_the_he.set("200")
    app.v_do_tre.set("50")
    app.bat_dau_chay()
    bom_su_kien(app, lambda: "Thế hệ" in app.o_log.get("1.0", "end"))
    assert app.worker is not None and app.worker.dang_chay
    app.dung_chay()
    bom_su_kien(app, lambda: app.ket_qua is not None and app.worker is None)
    assert app.ket_qua.bi_dung and app.ket_qua.so_the_he_da_chay < 200
    assert "BỊ DỪNG SỚM" in app.o_log.get("1.0", "end")


@pytest.mark.parametrize(
    "bien,gia_tri",
    [("v_so_ca_the", "abc"), ("v_so_the_he", "0"), ("v_ty_le_dot_bien", "2"), ("v_ty_le_lai_ghep", "-1"),
     ("v_do_tre", "x"), ("v_seed", "x")],
)
def test_ui_tham_so_sai_hien_loi_va_khong_chay(ung_dung, bien, gia_tri):
    app = ung_dung
    getattr(app, bien).set(gia_tri)
    app.bat_dau_chay()
    assert len(app.loi_hien) == 1
    assert app.worker is None


def test_ui_bai_toan_ngau_nhien(ung_dung):
    app = ung_dung
    app.v_nguon.set("N điểm ngẫu nhiên")
    app.v_so_diem.set("25")
    app.v_so_ca_the.set("30")
    app.v_so_the_he.set("10")
    app.v_do_tre.set("0")
    app.bat_dau_chay()
    bom_su_kien(app, lambda: app.ket_qua is not None and app.worker is None)
    assert len(app.ket_qua.tuyen_tot_nhat) == 25


def test_ui_dong_cua_so_khi_dang_chay(ung_dung):
    app = ung_dung
    app.v_so_the_he.set("1000")
    app.v_do_tre.set("50")
    app.bat_dau_chay()
    w = app.worker
    app.goc.update()
    app._khi_dong_cua_so()
    w._luong.join(timeout=5)
    assert not w.dang_chay

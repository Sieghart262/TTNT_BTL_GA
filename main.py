"""Điểm khởi chạy ứng dụng mô phỏng Giải thuật di truyền (GA) giải bài toán TSP.

Chạy: python main.py
"""

import tkinter as tk

from gui.app import UngDungGA


def main() -> None:
    """Tạo cửa sổ chính và chạy vòng lặp sự kiện Tkinter."""
    goc = tk.Tk()
    UngDungGA(goc)
    goc.mainloop()


if __name__ == "__main__":
    main()

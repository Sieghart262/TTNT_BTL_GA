# CLAUDE.md — Bài tập lớn Trí tuệ nhân tạo: Mô phỏng Giải thuật di truyền (GA)

## 1. Tổng quan dự án

- **Tên dự án:** Mô phỏng Giải thuật di truyền (Genetic Algorithm – GA)
- **Bài toán:** Người chào hàng (TSP) — tìm chu trình ngắn nhất đi qua đúng 1 lần mỗi địa điểm trong **15 địa danh nổi tiếng ở Hà Nội** rồi quay về điểm xuất phát.
- **Môn học:** Trí tuệ nhân tạo (NEU)
- **Mục tiêu:** Ứng dụng desktop cho phép nhập tham số GA, chạy thuật toán nền (không đơ giao diện), xem log thời gian thực và xem kết quả bằng đồ thị.

### Dữ liệu bài toán
- Dùng **toạ độ thật (vĩ độ, kinh độ)** của 15 địa danh, khoảng cách tính bằng **công thức Haversine** (km). Lưu trong `ga/data.py`.
- Danh sách (toạ độ gần đúng, cần kiểm tra lại trên Google Maps trước khi nộp báo cáo):
  Hồ Hoàn Kiếm, Lăng Bác, Văn Miếu – Quốc Tử Giám, Hồ Tây, Nhà hát Lớn, Bến xe Mỹ Đình, SVĐ Quốc gia Mỹ Đình, ĐH Bách khoa HN, ĐH Kinh tế Quốc dân, Ga Hà Nội, Royal City, Times City, Aeon Mall Long Biên, Cầu Long Biên, Công viên Thống Nhất.
- Lý do chọn: 15 điểm đủ nhỏ để chạy nhanh, đủ lớn (14!/2 ≈ 43 tỷ chu trình) để chứng minh GA hữu ích; toạ độ thật giúp báo cáo có ý nghĩa thực tế.
- Mở rộng (tuỳ chọn): nút "Tạo điểm ngẫu nhiên" với N tuỳ ý để thử độ co giãn của thuật toán.

## 2. Công nghệ

| Thư viện | Vai trò |
|---|---|
| Python 3.10+ | Ngôn ngữ chính |
| Tkinter (+ ttk) | Giao diện GUI |
| Matplotlib (`FigureCanvasTkAgg`) | Nhúng 2 biểu đồ vào giao diện |
| `threading` + `queue.Queue` | Chạy GA ở luồng nền, truyền log/kết quả về luồng giao diện an toàn |
| NumPy | Tính ma trận khoảng cách, tăng tốc |
| `random`, `math`, `dataclasses`, `typing` | Hỗ trợ GA, type hint |
| pytest (tuỳ chọn) | Kiểm thử phần logic GA |

Cài đặt: `pip install matplotlib numpy` (Tkinter đi kèm Python trên Windows).

## 3. Cấu trúc thư mục

```
TTNT_BTL_GA/
├── CLAUDE.md
├── requirements.txt
├── main.py                 # Điểm khởi chạy, chỉ tạo cửa sổ và chạy mainloop
├── ga/                     # LOGIC THUẬT TOÁN — KHÔNG import tkinter / matplotlib
│   ├── __init__.py
│   ├── data.py             # 15 địa điểm, hàm Haversine, ma trận khoảng cách
│   ├── operators.py        # Khởi tạo, chọn lọc, lai ghép OX, đột biến, elitism
│   └── algorithm.py        # Lớp GeneticAlgorithm, vòng lặp tiến hoá
├── gui/                    # LOGIC GIAO DIỆN — KHÔNG chứa thuật toán GA
│   ├── __init__.py
│   ├── app.py              # Cửa sổ chính, bố cục, nút Start/Stop, xử lý sự kiện
│   ├── plots.py            # Vẽ biểu đồ hội tụ và bản đồ 2D
│   └── worker.py           # Thread chạy GA, đẩy dữ liệu vào Queue
├── tests/                  # Test cho ga/ (tuỳ chọn)
└── docs/                   # Ảnh chụp màn hình, nội dung báo cáo
```

## 4. Quy tắc BẮT BUỘC (không được vi phạm)

1. **Nhập tham số:** Giao diện có ô nhập cho **số cá thể, số thế hệ, tỷ lệ đột biến, tỷ lệ lai ghép**. Phải kiểm tra hợp lệ (số nguyên dương; tỷ lệ trong [0, 1]) và báo lỗi bằng `messagebox`, không để chương trình crash.
2. **Log thời gian thực:** Mọi bước trung gian (khởi tạo quần thể, fitness/quãng đường tốt nhất và trung bình mỗi thế hệ, số lần lai ghép/đột biến, cải thiện mới…) được ghi vào `ScrolledText` trên giao diện, tự cuộn xuống cuối.
3. **Threading:** Vòng lặp GA **luôn chạy trong thread riêng** (`daemon=True`). Thread nền **không được gọi trực tiếp** widget Tkinter; chỉ `queue.put(...)`, còn luồng chính dùng `root.after(ms, poll_queue)` để lấy dữ liệu và cập nhật UI. Có nút **Dừng** (dùng `threading.Event`) và vô hiệu hoá nút Chạy khi đang chạy.
4. **Hai biểu đồ khi chạy xong** (đặt trong giao diện, không mở cửa sổ Matplotlib riêng):
   - Biểu đồ 1: **hội tụ fitness** — quãng đường tốt nhất (và trung bình) theo thế hệ, quãng đường giảm dần.
   - Biểu đồ 2: **bản đồ 2D** — vẽ các địa điểm (kèm nhãn) và nối theo thứ tự tuyến đường tốt nhất, có mũi tên/đánh số thứ tự, khép kín về điểm đầu.
5. **Tách biệt logic:** Thư mục `ga/` tuyệt đối không import `tkinter`/`matplotlib`; `gui/` không chứa phép chọn lọc/lai/đột biến. GA giao tiếp với giao diện qua **callback** (`on_generation(gen, best, avg, route)`) hoặc generator, để có thể test GA độc lập bằng dòng lệnh.
6. **Comment và docstring bằng tiếng Việt** cho mọi module, lớp, hàm (mô tả mục đích, tham số, giá trị trả về, ý nghĩa thuật toán) để đưa trực tiếp vào báo cáo. Tên biến/hàm vẫn viết tiếng Anh `snake_case`.

## 5. Thiết kế thuật toán GA (mặc định, có thể chỉnh)

- **Biểu diễn cá thể:** hoán vị các chỉ số địa điểm `[0..14]` (path representation).
- **Fitness:** `fitness = 1 / tổng_quãng_đường` (càng lớn càng tốt); hiển thị trên đồ thị dưới dạng quãng đường (km) cho dễ hiểu.
- **Khởi tạo:** quần thể hoán vị ngẫu nhiên.
- **Chọn lọc:** Tournament selection (kích thước giải đấu = 3–5); có thể thêm lựa chọn Roulette để so sánh.
- **Lai ghép:** Order Crossover (OX), áp dụng với xác suất = tỷ lệ lai ghép.
- **Đột biến:** Swap hoặc Inversion, mỗi cá thể với xác suất = tỷ lệ đột biến.
- **Elitism:** giữ lại 1–2 cá thể tốt nhất qua mỗi thế hệ.
- **Dừng:** đạt số thế hệ tối đa hoặc người dùng bấm Dừng.
- **Tham số gợi ý:** 100 cá thể, 300 thế hệ, đột biến 0.02–0.1, lai ghép 0.8–0.9.
- **Tái lập kết quả:** cho phép nhập `seed` (tuỳ chọn).

## 6. Bố cục giao diện gợi ý

```
+--------------------------+--------------------------------------+
| Khung tham số            |  Biểu đồ hội tụ (Matplotlib)         |
|  - Số cá thể             |                                      |
|  - Số thế hệ             +--------------------------------------+
|  - Tỷ lệ đột biến        |  Bản đồ 2D tuyến đường tốt nhất      |
|  - Tỷ lệ lai ghép        |                                      |
|  [Chạy] [Dừng] [Đặt lại] |                                      |
+--------------------------+--------------------------------------+
| Log thời gian thực (ScrolledText)  | Thanh trạng thái / tiến độ  |
+-------------------------------------------------------------------+
```

## 7. Quy ước code

- Tuân thủ PEP 8, type hint cho hàm công khai, mỗi hàm ngắn và một nhiệm vụ.
- Không dùng biến toàn cục cho trạng thái GA; dùng lớp/`dataclass` (ví dụ `GAConfig`, `GAResult`).
- Không dùng `time.sleep` trong luồng giao diện; nếu cần làm chậm để quan sát, đặt trong thread nền (tham số "độ trễ mỗi thế hệ", tuỳ chọn).
- Giới hạn tần suất vẽ lại biểu đồ khi đang chạy (ví dụ mỗi 5–10 thế hệ) để GUI mượt; vẽ đầy đủ khi kết thúc.
- Khi đóng cửa sổ phải dừng thread nền (`stop_event.set()`).
- Xử lý ngoại lệ ở thread nền và gửi thông báo lỗi qua Queue.

## 8. Lệnh thường dùng

```bash
pip install -r requirements.txt   # Cài thư viện
python main.py                    # Chạy ứng dụng
pytest tests/                     # Chạy kiểm thử (nếu có)
```

## 9. Kiểm tra trước khi nộp (Definition of Done)

- [ ] Nhập được 4 tham số, có kiểm tra hợp lệ
- [ ] Log hiện theo thời gian thực, giao diện không đơ khi chạy
- [ ] Có nút Dừng hoạt động, đóng cửa sổ không treo tiến trình
- [ ] Hiện đủ 2 biểu đồ trên giao diện sau khi chạy xong
- [ ] `ga/` không import tkinter/matplotlib; `gui/` không chứa logic GA
- [ ] Mọi module/lớp/hàm có docstring tiếng Việt
- [ ] Chụp ảnh màn hình và ghi kết quả thử nghiệm với nhiều bộ tham số vào `docs/` cho báo cáo

## 10. Hướng mở rộng (nếu còn thời gian)

- So sánh các toán tử (Tournament vs Roulette, Swap vs Inversion, OX vs PMX).
- Hoạt ảnh tuyến đường tốt nhất cập nhật theo thế hệ.
- So sánh kết quả GA với thuật toán Nearest Neighbor và (vì N=15) lời giải tối ưu bằng Held–Karp.
- Xuất log và biểu đồ ra file CSV/PNG.
- Nền bản đồ thật bằng ảnh tĩnh của Hà Nội phía sau các điểm.

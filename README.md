# ENFOLUX — Bộ nhận diện (logo · favicon · ảnh chia sẻ)

Mở **`xem-truoc.html`** trong trình duyệt để xem 3 hướng logo trên nền trắng, nền `#14302A`, ở cỡ lớn và ở cao 32 px.
Tải trọn bộ: **`enfolux-brand-kit.zip`**.

## 3 hướng logo

| Hướng | Thư mục | Ý nghĩa |
|---|---|---|
| **A. Wordmark thuần** | `huong-a-wordmark/` | Chữ "enfolux" Montserrat 600. Lòng chữ "o" chứa một **hạt màu đồng**: hạt nguyên liệu, cũng là điểm sáng "lux". Gọn, dễ nhớ, đọc rõ nhất ở cỡ nhỏ. |
| **B. Biểu tượng + wordmark** | `huong-b-bieu-tuong/` | Chữ "e" hình học, nét mở ở góc dưới phải và **một giọt chiết xuất màu đồng** rơi ra: tinh dầu, hương liệu, sự chắt lọc. Biểu tượng tách riêng được cho bao bì, tem, favicon. |
| **C. Monogram "e"** | `huong-c-monogram/` | Chữ "e" trong khung vuông bo nhẹ, dưới có **vạch định lượng màu quế** như mép muỗng gạt phẳng: đong đúng, chuẩn xác. Đậm, chắc, nổi bật nhất khi làm favicon/app icon. |

## Danh sách file (giống nhau ở mỗi thư mục)

| File | Thông số |
|---|---|
| `logo-horizontal.svg` / `.png` | PNG nền trong suốt, cao 256 px, tỷ lệ ≤ 5:1 (A 4,83 · B 4,90 · C 4,92). Dùng cho header nền trắng |
| `logo-horizontal-dark.svg` / `.png` | Như trên, chữ kem `#FAF6F0` + nhấn quế `#C8782E`, cho footer `#14302A` |
| `logo-horizontal@2x.png`, `logo-horizontal-dark@2x.png` | Cao 512 px, cho màn hình độ phân giải cao |
| `logo-horizontal-1mau.svg` / `.png` | Bản 1 màu (forest) |
| `logo-mark.svg` / `.png` | Biểu tượng vuông (PNG 512×512, nền trong suốt) |
| `favicon.png` | 512×512, nền forest `#1F4D3A`, lề an toàn 12% |
| `favicon.ico` | 16 / 32 / 48 px |
| `apple-touch-icon.png` | 180×180, nền đặc |
| `og-image.png` | 1200×630, nền kem `#FAF6F0` |
| `og-image-dark.png` | 1200×630, nền forest-900 `#14302A` |
| `_kiem-tra/favicon-16/32/48.png` | Ảnh thu nhỏ để kiểm tra độ đọc |

Mọi chữ trong SVG đã chuyển thành nét (outline), không cần cài font.
Ảnh OG: toàn bộ logo và chữ nằm trong ô vuông 630×630 ở giữa, cách mép ô ≥ 60 px, nên Facebook/Zalo cắt vuông vẫn đủ.

## Bảng màu

| Tên | Mã | Dùng |
|---|---|---|
| Forest 700 | `#1F4D3A` | Màu chính của logo, nền favicon |
| Forest 900 | `#14302A` | Nền footer tối, nền OG tối |
| Navy | `#1C3557` | Hạn chế, không dùng trong logo |
| Đồng | `#A85F22` | Điểm nhấn trên nền sáng (≤ 5% diện tích) |
| Quế | `#C8782E` | Điểm nhấn trên nền tối |
| Trắng | `#FFFFFF` | Nền |
| Kem | `#FAF6F0` | Nền, chữ logo trên nền tối |
| Kem đậm | `#F3ECE1` | Nền phụ |
| Chữ đậm | `#1B1F1D` | Văn bản |

Quy tắc nhanh: nền sáng → forest + đồng. Nền tối → kem + quế. Không có màu nào khác trong logo.

## Hướng dẫn sử dụng

**Khoảng trống tối thiểu.** Gọi **x** là chiều cao chữ "n" trong wordmark. Giữ khoảng trống ≥ **1x** ở cả 4 phía logo, không đặt chữ, ảnh hay mép khung vào vùng này. Với biểu tượng đứng riêng: khoảng trống ≥ 25% cạnh biểu tượng.

**Cỡ nhỏ nhất.**
- Logo ngang: cao **24 px** (hướng A) / **28 px** (hướng B, C) trên màn hình; in ấn rộng ≥ **25 mm**.
- Biểu tượng / favicon: **16 px**; in ≥ **6 mm**.
- Dưới các cỡ trên, dùng biểu tượng thay cho logo ngang.

**Nền.** Nền trắng, kem, kem đậm → bản thường. Nền forest/forest-900 hoặc ảnh tối → bản `-dark`. Ảnh nhiều chi tiết → đặt logo lên một mảng màu đặc.

**Không được:**
- Kéo méo, bóp ngang/dọc. Luôn khoá tỷ lệ khi thay đổi kích thước.
- Đổi màu ngoài bảng màu, đổi màu riêng từng chữ, đổi chỗ màu đồng sang phần chữ.
- Thêm bóng đổ, viền, gradient, hiệu ứng 3D, ánh kim.
- Xoay, nghiêng, viết lại bằng font khác, chỉnh khoảng cách chữ.
- Bỏ hạt/giọt/vạch đồng rồi thay bằng hình khác; phóng to điểm nhấn.
- Đặt bản sáng lên nền tối hoặc ngược lại.

## Dựng lại file

```bash
pip install fonttools cairosvg pillow
python3 source/build.py
```

Font: Montserrat (SIL Open Font License), lấy từ gói `@fontsource/montserrat`, nằm trong `source/fonts/`.

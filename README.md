# 🏫 CAMS — Classroom Allocation Management System

> **Hệ thống Quản lý và Xếp phòng học Tự động theo Thời khóa biểu**  
> **Học phần:** Đảm bảo Chất lượng Phần mềm theo hướng Scrum  
> **Đơn vị thực hiện:** Nhóm 6  
> **Website Demo Online:** `https://cams-nhom6.vercel.app`

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Backend-Python%203.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2F%20Vite-61dafb.svg)](https://react.dev/)

---

## 👥 THÀNH VIÊN NHÓM & PHÂN CÔNG VAI TRÒ

| STT | Họ và Tên | Vai trò Scrum | Chức danh kỹ thuật | Nhiệm vụ chính |
|:---:|---|---|---|---|
| 1 | **Trần Ngọc Duy** *(22110110)* | **Product Owner** | Project Lead | Quản lý Product Backlog, User Stories, Acceptance Criteria & nghiệm thu UAT. |
| 2 | **Phan Quang Hoàng** | **ScrumMaster** / Dev | Algorithm Lead | Điều phối Daily Scrum; lập trình Auto Allocation Engine (Greedy Best-fit) & bộ kiểm tra ràng buộc dùng chung. |
| 3 | **Phạm Minh Giang** | Development Team | Backend & Database | Thiết kế CSDL SQLAlchemy, API CRUD phòng/lớp/buổi học & xử lý Excel TKB. |
| 4 | **Phạm Minh Quang** | Development Team | Frontend & UI/UX | Thiết kế giao diện Figma Make, bảng lưới TKB trực quan, màn hình tra cứu responsive 375px. |
| 5 | **Đặng Huy Hoàng** | Development Team | **Full-stack / DevOps** | **Xác thực & RBAC 04 vai trò, tích hợp luồng End-to-End, API Tra cứu & Thống kê, Audit Log, Closure Policy & triển khai Web Online.** |
| 6 | **Nghiêm Vũ Hải** | Development Team | QA / Tester Lead | Chuẩn bị dữ liệu mẫu biên, thiết kế Test Cases, kiểm thử tích hợp/hồi quy & ghi nhật ký Scrum. |

---

## 🔑 TÀI KHOẢN DEMO 04 VAI TRÒ (RBAC)

Khi khởi chạy Backend lần đầu (`AUTO_SEED=true`), hệ thống tự động khởi tạo sẵn bộ dữ liệu mẫu gồm **11 phòng học**, **12 lớp học phần**, **14 buổi học** (trong đó có 8 buổi chờ xếp phòng để thử nghiệm ngay nút **⚡ Tự động xếp phòng**) và **04 tài khoản phân quyền**:

| Vai trò | Username | Mật khẩu | Quyền hạn chính |
|---|---|---|---|
| **Admin** (`ADMIN`) | `admin` | `123` | Toàn quyền hệ thống, Quản lý Tài khoản & RBAC (`ADM-01`), Cấu hình Closure Dates (`ADM-04`), Xem Audit Logs (`ADM-05`). |
| **Cán bộ Đào tạo** (`OFFICER`) | `officer01` | `123` | Import/Export Excel TKB (`OFF-01`, `OFF-08`), Chạy **⚡ Tự động xếp phòng** (`OFF-02`), Điều chỉnh phòng trên Lưới TKB (`OFF-03..06`), Duyệt đơn đổi phòng (`OFF-07`), Xem Thống kê. |
| **Giảng viên** (`LECTURER`) | `gv_an` | `123` | Xem lịch giảng dạy cá nhân (`LEC-01`), Tra cứu phòng trống (`LEC-02`), Gửi đơn xin đổi phòng trực tuyến (`LEC-03`) & Theo dõi trạng thái duyệt (`LEC-04`). |
| **Sinh viên** (`STUDENT`) | `sv_minhanh` | `123` | Tra cứu TKB cá nhân theo MSSV `21021234` / `SV001` (`STU-01`), Tìm phòng trống tự học (`STU-02`), Nhận thông báo biến động phòng (`STU-03`), Báo cáo sự cố. |

> 💡 **Tra cứu công khai không cần đăng nhập (`STU-01`):** Tại màn hình Đăng nhập, nhập trực tiếp MSSV `21021234` hoặc `SV001` vào ô tra cứu nhanh để xem ngay thời khóa biểu.

---

## ✨ TÍNH NĂNG CỐT LÕI & QUY TẮC NGHIỆP VỤ

* **Auto Allocation Engine (`POST /api/allocation/run`):** Giải thuật **Greedy Best-fit** sắp xếp lớp theo độ khó giảm dần (nhiều thiết bị đặc thù → sĩ số đông) và chọn phòng nhỏ nhất thỏa mãn đồng thời sức chứa, loại phòng, thiết bị, không trùng ca phòng và không trùng lịch giảng viên. Hỗ trợ cả chế độ **Xem trước (`apply=false`)** và **Áp dụng lưu DB (`apply=true`)**.
* **BR-01 — Chống trùng phòng tuyệt đối:** Mọi thao tác gán/đổi phòng thủ công hoặc duyệt đơn đều đi qua hàm `validate_assignment` dùng chung; chặn cứng lỗi `409 Conflict` kèm tên lớp đang chiếm phòng.
* **BR-02 — Kiểm soát sức chứa & Cảnh báo quá tải:** Tự động xếp phòng luôn đảm bảo `Sức chứa >= Sĩ số`; khi điều chỉnh thủ công vào phòng nhỏ hơn sĩ số, hệ thống bật hộp thoại cảnh báo vàng nêu rõ số ghế thiếu trước khi cho phép xác nhận.
* **BR-03 — Chính sách Khóa thời hạn (`First` & `Final Closure Date`):** Quá `First Closure Date` tự động khóa nạp file Excel và xếp tự động; quá `Final Closure Date` chuyển sang chế độ `Read-only` khóa đổi phòng và đơn xin đổi phòng.
* **BR-04 — Nhật ký Kiểm toán bất biến (`Audit Trail`):** Tự động ghi vết mọi thao tác Import, Xếp phòng tự động, Đổi phòng thủ công, Duyệt/Từ chối đơn và Quản trị tài khoản tại `/api/audit-logs` (chỉ đọc, không thể sửa/xóa).
* **Tương thích Figma Make Preview:** Frontend tự động nhận diện kết nối Backend (`VITE_API_URL`); nếu mở trong môi trường preview tĩnh của Figma Make sẽ tự động chuyển sang dữ liệu mẫu dự phòng mà không vỡ giao diện.

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY LOCAL

### Bước 1: Thiết lập & Chạy Backend (FastAPI)
```bash
cd backend
python -m venv venv

# Kích hoạt môi trường ảo (Windows PowerShell):
.\venv\Scripts\Activate.ps1
# Hoặc trên macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```
* Swagger API Docs: `http://localhost:8000/docs`

### Bước 2: Thiết lập & Chạy Frontend (React + Vite)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
* Giao diện Web chạy tại: `http://localhost:8443` (cấu hình chuẩn tương thích Figma Make; hoặc chạy `npx vite --port 5173` cho cổng `5173`).

### Bước 3: Chạy Bộ Kiểm thử Tự động (Unit + API Integration Tests)
```bash
cd backend
pytest -v
```

---

## ☁️ HƯỚNG DẪN TRIỂN KHAI WEB ONLINE (RENDER + VERCEL)

1. **Backend (Render):**
   * Kết nối kho GitHub vào Render sử dụng file cấu hình [render.yaml](render.yaml) (hoặc đặt `Root Directory = backend`, `Build Command = pip install -r requirements.txt`, `Start Command = uvicorn main:app --host 0.0.0.0 --port $PORT`).
   * Đặt biến môi trường `AUTO_SEED=true`, `SECRET_KEY=<chuỗi-bí-mật>`, `CORS_ORIGINS=https://<ten-mien-frontend>.vercel.app`.
2. **Frontend (Vercel):**
   * Import kho GitHub vào Vercel, chọn `Root Directory = frontend` (đã có sẵn [frontend/vercel.json](frontend/vercel.json)).
   * Thêm biến môi trường `VITE_API_URL=https://<ten-service-backend>.onrender.com` rồi bấm **Deploy**.

---

## 📄 GIẤY PHÉP (LICENSE)
Dự án được phân phối dưới giấy phép [MIT License](LICENSE). Bản quyền © 2026 Nhóm 6.

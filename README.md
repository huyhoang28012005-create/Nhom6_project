# 🏫 CAMS — Classroom Allocation Management System
> **Hệ thống Quản lý và Xếp phòng học cho Sinh viên**  
> **Học phần:** Đảm bảo Chất lượng Phần mềm theo hướng Scrum (12 tuần / 4 Sprints)  
> **Đơn vị thực hiện:** Nhóm 6  
> **Website Demo Online:** `https://cams-nhom6.vercel.app` *(Đang cập nhật)*

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Backend-Python%203.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2F%20Vite-61dafb.svg)](https://react.dev/)

---

## 👥 THÀNH VIÊN NHÓM & PHÂN CÔNG VAI TRÒ

| STT | Họ và Tên | Vai trò Scrum | Chức danh kỹ thuật | Nhiệm vụ chính |
|:---:|---|---|---|---|
| 1 | **Trần Ngọc Duy** *(22110110)* | **Product Owner** | Project Lead | Làm chủ đặc tả, quản lý Product Backlog, chuẩn bị dữ liệu mẫu, nghiệm thu DoD. |
| 2 | **Phan Quang Hoàng** | **ScrumMaster** / Dev | Algorithm Lead | Chủ trì Daily Scrum, lập trình Engine tự động xếp phòng & kiểm tra trùng lịch (BR-01, BR-02). |
| 3 | **Phạm Minh Giang** | Development Team | Backend & Database | Thiết kế CSDL, lập trình API CRUD phòng, module đọc/ghi file Excel TKB. |
| 4 | **Phạm Minh Quang** | Development Team | Frontend & UI/UX | Thiết kế giao diện Figma, lập trình bảng lưới TKB trực quan, màn hình tra cứu responsive. |
| 5 | **Đặng Huy Hoàng** | Development Team | **Full-stack / DevOps** | **Quản trị GitHub, tích hợp luồng API-UI, bảo mật RBAC và triển khai Web Online.** |
| 6 | **Nghiêm Vũ Hải** | Development Team | QA / Tester Lead | Soạn dữ liệu test mẫu, thiết kế Test Cases, kiểm thử manual và ghi chép nhật ký Scrum. |

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY LOCAL (GETTING STARTED)

### Yêu cầu tiên quyết
* **Git**: Phiên bản 2.30+
* **Python**: Phiên bản 3.10 trở lên
* **NodeJS**: Phiên bản 18.x trở lên (nếu chạy frontend)

---

### Bước 1: Clone kho mã nguồn về máy
```bash
git clone https://github.com/binc95145-hue/CAMS-Nhom6.git
cd CAMS-Nhom6
```

### Bước 2: Thiết lập Backend (Python)
```bash
# Di chuyển vào thư mục backend
cd backend

# Khởi tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Trên Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Trên macOS / Linux:
source venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Tạo file cấu hình môi trường từ mẫu
cp .env.example .env

# Chạy server Backend
uvicorn main:app --reload --port 8000
```
> Backend API Swagger docs sẽ chạy tại: `http://localhost:8000/docs`

---

### Bước 3: Thiết lập Frontend
```bash
# Mở một terminal mới và vào thư mục frontend
cd frontend

# Cài đặt các gói phụ thuộc
npm install

# Tạo file môi trường
cp .env.example .env

# Chạy server Frontend
npm run dev
```
> Giao diện web sẽ chạy tại: `http://localhost:5173`

---

## 🌳 QUY ƯỚC NHÁNH (GIT BRANCHING POLICY)

Hệ thống áp dụng mô hình Gitflow tinh giản để đảm bảo an toàn mã nguồn:

```text
main (Chỉ chứa code ổn định, dùng để Demo và Deploy production)
  │
  └── develop (Nhánh tích hợp chính của cả nhóm)
        ├── feature/be-database (Nhánh làm việc của Giang)
        ├── feature/algorithm-engine (Nhánh làm việc của Hoàng SM)
        ├── feature/fe-timetable-grid (Nhánh làm việc của Quang)
        └── feature/devops-integration (Nhánh của Đặng Huy Hoàng)
```

### Quy tắc làm việc:
1. **Tuyệt đối không commit trực tiếp lên `main` và `develop`**.
2. Mọi tính năng mới bắt buộc phải tạo nhánh từ `develop`: `git checkout -b feature/<ten-tinh-nang>`.
3. Khi hoàn thành, tạo **Pull Request (PR)** trỏ về nhánh `develop`.
4. Bắt buộc phải có **ít nhất 1 thành viên review và approve** mới được gộp (merge) code.

---

## 📌 QUY ƯỚC COMMIT MESSAGE (CONVENTIONAL COMMITS)

* `feat`: Thêm một tính năng mới (vd: `feat: add room allocation api`)
* `fix`: Sửa lỗi phát sinh (vd: `fix: prevent double booking on same shift`)
* `docs`: Thêm hoặc chỉnh sửa tài liệu (vd: `docs: update deployment instructions`)
* `test`: Thêm hoặc cập nhật Test Cases (vd: `test: add collision check test cases`)
* `refactor`: Tái cấu trúc mã nguồn nhưng không đổi chức năng

---

## 📄 GIẤY PHÉP (LICENSE)
Dự án được phân phối dưới giấy phép [MIT License](LICENSE). Bản quyền © 2026 Nhóm 6.

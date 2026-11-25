# Đặc tả Auto Allocation Engine (Greedy Best-fit)

Phụ trách: Phan Quang Hoàng · Mã nguồn: `backend/allocation/`

## 1. Đối tượng
- **Buổi học cần xếp** = một dòng `timetable_sessions` chưa có `room_id`, kèm thông tin lớp (`course_classes`).
- **Booking cố định** = các buổi đã có phòng; engine không thay đổi chúng.

## 2. Ràng buộc cứng (hàm duy nhất `validate_assignment`)
| Mã | Quy tắc |
|---|---|
| `INVALID_DATA` | sĩ số > 0; thứ 1–7; giờ kết thúc > giờ bắt đầu |
| `ROOM_CAPACITY` | sức chứa phòng ≥ sĩ số |
| `ROOM_TYPE` | `room_type` phòng = `required_room_type` của lớp |
| `ROOM_EQUIPMENT` | thiết bị yêu cầu ⊆ thiết bị phòng (không phân biệt hoa/thường, tách bằng dấu phẩy) |
| `ROOM_TIME_CONFLICT` | cùng phòng, cùng thứ, khoảng [bắt đầu, kết thúc) giao nhau → trùng. Sát nhau (9:00–9:00) không trùng |
| `LECTURER_TIME_CONFLICT` | cùng giảng viên, cùng thứ, giờ giao nhau. Bỏ qua nếu chưa có dữ liệu giảng viên |

Đổi phòng thủ công gọi cùng hàm với `ignore_session_id` = buổi đang sửa.

## 3. Thuật toán
1. Tách các buổi dữ liệu không hợp lệ vào `invalid` (không làm hỏng cả lượt).
2. Sắp xếp theo độ khó giảm dần: số thiết bị yêu cầu ↓, sĩ số ↓, rồi thứ/giờ/mã lớp/id để kết quả tái lập.
3. Với mỗi buổi, duyệt phòng từ nhỏ đến lớn (sức chứa, mã phòng); phòng đầu tiên qua `validate_assignment` là best-fit.
4. Chọn xong thì thêm vào danh sách booking để các buổi sau tránh trùng.
5. Không có phòng → `unassigned` kèm lý do.

Độ phức tạp ≈ O(n log n + n·m·b).
Giới hạn: tham lam nên không đảm bảo tối ưu toàn cục; có thể bỏ sót lời giải tồn tại khi các lớp cạnh tranh phòng phức tạp.

## 4. Lý do không xếp được
`NO_ROOMS`, `ROOM_TYPE` (không có phòng loại đó), `ROOM_CAPACITY` (nêu sức chứa lớn nhất), `ROOM_EQUIPMENT`,
`ROOM_TIME_CONFLICT` (nêu số phòng phù hợp đều bận), `LECTURER_TIME_CONFLICT`.

## 5. API
- `POST /api/allocation/run` body `{ "session_ids": [..] | null, "apply": false }`
  → `{ applied, summary, assigned[], unassigned[], invalid[] }`. `apply=false` chỉ xem trước.
- `POST /api/allocation/validate` body `{ "session_id", "room_id" }` → `{ valid, violations[] }`.

## 6. Việc cần phối hợp
- **Giang (DB):** `course_classes` chưa có cột giảng viên. Thêm `lecturer` (String) thì ràng buộc giảng viên tự bật, không cần sửa engine.
- **Đặng (API):** các endpoint tạo/sửa/import buổi học trong `main.py` đang lặp lại logic kiểm tra 3 lần; nên thay bằng `validate_assignment`.
- **Hải (QA):** chạy `cd backend && pytest`; thêm dữ liệu thực nghiệm để tối ưu.

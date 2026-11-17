"""Bộ kiểm tra ràng buộc DÙNG CHUNG cho xếp tự động và đổi phòng thủ công.

Mọi nơi muốn gán/đổi phòng đều phải đi qua `validate_assignment` để không có
chuyện thuật toán hợp lệ nhưng thao tác chỉnh tay lại tạo xung đột.
"""

from __future__ import annotations

from datetime import time
from typing import Iterable

from .types import Booking, Room, SessionRequest, Violation, ViolationCode


def times_overlap(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    """Hai khoảng nửa mở [start, end) giao nhau. Khớp với truy vấn trong main.py."""
    return a_start < b_end and a_end > b_start


def validate_request_data(req: SessionRequest) -> list[Violation]:
    """Kiểm tra dữ liệu đầu vào của buổi học (không liên quan phòng)."""
    errs: list[Violation] = []
    if req.student_count is None or req.student_count <= 0:
        errs.append(Violation(ViolationCode.INVALID_DATA, "Sĩ số phải lớn hơn 0"))
    if not 1 <= req.weekday <= 7:
        errs.append(Violation(ViolationCode.INVALID_DATA, "Thứ trong tuần phải từ 1 đến 7"))
    if req.end_time <= req.start_time:
        errs.append(Violation(ViolationCode.INVALID_DATA, "Giờ kết thúc phải sau giờ bắt đầu"))
    return errs


def check_static(req: SessionRequest, room: Room) -> list[Violation]:
    """Ràng buộc không phụ thuộc lịch: sức chứa, loại phòng, thiết bị."""
    errs: list[Violation] = []
    if room.capacity < req.student_count:
        errs.append(
            Violation(
                ViolationCode.ROOM_CAPACITY,
                f"Sức chứa phòng {room.code} không đủ ({room.capacity} < {req.student_count})",
            )
        )
    if room.room_type != req.required_room_type:
        errs.append(
            Violation(
                ViolationCode.ROOM_TYPE,
                f"Loại phòng {room.code} là '{room.room_type}', lớp yêu cầu '{req.required_room_type}'",
            )
        )
    missing = req.required_equipment - room.equipment
    if missing:
        errs.append(
            Violation(
                ViolationCode.ROOM_EQUIPMENT,
                f"Phòng {room.code} thiếu thiết bị: {', '.join(sorted(missing))}",
            )
        )
    return errs


def check_lecturer(
    req: SessionRequest,
    bookings: Iterable[Booking],
    ignore_session_id: int | None = None,
) -> list[Violation]:
    """Giảng viên không được dạy hai buổi trùng giờ (độc lập với phòng)."""
    if not req.lecturer:
        return []
    for b in bookings:
        if b.session_id == ignore_session_id or b.session_id == req.session_id:
            continue
        if (
            b.lecturer
            and b.lecturer.casefold() == req.lecturer.casefold()
            and b.weekday == req.weekday
            and times_overlap(req.start_time, req.end_time, b.start_time, b.end_time)
        ):
            return [
                Violation(
                    ViolationCode.LECTURER_TIME_CONFLICT,
                    f"Giảng viên {req.lecturer} đã có lịch dạy trùng khung giờ này",
                )
            ]
    return []


def check_room_time(
    req: SessionRequest,
    room: Room,
    bookings: Iterable[Booking],
    ignore_session_id: int | None = None,
) -> list[Violation]:
    """Phòng không được bị trùng ca."""
    for b in bookings:
        if b.session_id == ignore_session_id or b.session_id == req.session_id:
            continue
        if (
            b.room_id == room.id
            and b.weekday == req.weekday
            and times_overlap(req.start_time, req.end_time, b.start_time, b.end_time)
        ):
            return [
                Violation(
                    ViolationCode.ROOM_TIME_CONFLICT,
                    f"Phòng {room.code} đã có lịch vào khung giờ này",
                )
            ]
    return []


def validate_assignment(
    req: SessionRequest,
    room: Room,
    bookings: Iterable[Booking],
    ignore_session_id: int | None = None,
) -> list[Violation]:
    """Hàm validate duy nhất. Trả về danh sách vi phạm; rỗng nghĩa là hợp lệ.

    - `bookings`: các buổi học đã có phòng (DB + đã xếp trong lượt chạy).
    - `ignore_session_id`: dùng khi ĐỔI PHÒNG để buổi đang sửa không tự xung đột với chính nó.
    """
    bookings = list(bookings)
    return (
        validate_request_data(req)
        + check_static(req, room)
        + check_room_time(req, room, bookings, ignore_session_id)
        + check_lecturer(req, bookings, ignore_session_id)
    )

"""Auto Allocation Engine — Greedy Best-fit.

Thuật toán:
1. Loại các buổi học có dữ liệu không hợp lệ (đưa vào `invalid`, không làm hỏng cả lượt).
2. Sắp xếp theo độ khó giảm dần: nhiều thiết bị đặc thù hơn -> sĩ số lớn hơn.
   (Tie-break ổn định: ngày, giờ, mã lớp, session_id để kết quả tái lập được.)
3. Với mỗi buổi, lọc các phòng qua `validate_assignment` (cùng hàm với đổi phòng thủ công),
   rồi chọn phòng NHỎ NHẤT còn đáp ứng (Best-fit) để giảm lãng phí chỗ ngồi.
4. Không chọn được phòng -> `unassigned` kèm lý do cụ thể.

Độ phức tạp: O(n log n + n·m·b) với n buổi, m phòng, b số booking; đủ cho quy mô đồ án.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from .constraints import (
    check_lecturer,
    check_static,
    validate_assignment,
    validate_request_data,
)
from .types import (
    AllocationResult,
    Booking,
    Placement,
    Room,
    SessionRequest,
    Unplaced,
    Violation,
    ViolationCode,
)


def difficulty_key(req: SessionRequest):
    """Khoá sắp xếp: lớp khó xếp đứng trước."""
    return (
        -len(req.required_equipment),
        -req.student_count,
        req.weekday,
        req.start_time,
        req.class_code,
        req.session_id,
    )


def best_fit_key(room: Room):
    """Phòng nhỏ nhất trước; hoà thì theo mã phòng để kết quả ổn định."""
    return (room.capacity, room.code, room.id)


def explain_failure(
    req: SessionRequest,
    rooms: Sequence[Room],
    bookings: Sequence[Booking],
) -> tuple[Violation, ...]:
    """Tạo lý do cụ thể vì sao buổi học không xếp được."""
    if not rooms:
        return (Violation(ViolationCode.NO_ROOMS, "Hệ thống chưa có phòng học nào"),)

    # Giảng viên bận -> đổi phòng cũng vô ích, nêu thẳng nguyên nhân.
    lecturer_v = check_lecturer(req, bookings)
    if lecturer_v:
        return tuple(lecturer_v)

    suitable = [r for r in rooms if not check_static(req, r)]
    if suitable:
        return (
            Violation(
                ViolationCode.ROOM_TIME_CONFLICT,
                f"Cả {len(suitable)} phòng phù hợp đều đã có lịch vào khung giờ này",
            ),
        )

    # Không phòng nào qua ràng buộc tĩnh: nêu lý do chính theo từng loại.
    counts: Counter[ViolationCode] = Counter()
    for r in rooms:
        for v in check_static(req, r):
            counts[v.code] += 1

    reasons: list[Violation] = []
    n = len(rooms)
    same_type = [r for r in rooms if r.room_type == req.required_room_type]
    if not same_type:
        reasons.append(
            Violation(
                ViolationCode.ROOM_TYPE,
                f"Không có phòng loại '{req.required_room_type}' trong hệ thống",
            )
        )
    else:
        biggest = max(r.capacity for r in same_type)
        if biggest < req.student_count:
            reasons.append(
                Violation(
                    ViolationCode.ROOM_CAPACITY,
                    f"Không đủ sức chứa: lớp {req.student_count} SV, "
                    f"phòng '{req.required_room_type}' lớn nhất chỉ {biggest} chỗ",
                )
            )
        if req.required_equipment:
            fit_cap = [r for r in same_type if r.capacity >= req.student_count]
            if fit_cap and all(req.required_equipment - r.equipment for r in fit_cap):
                need = ", ".join(sorted(req.required_equipment))
                reasons.append(
                    Violation(
                        ViolationCode.ROOM_EQUIPMENT,
                        f"Không phòng nào đủ sức chứa mà có thiết bị: {need}",
                    )
                )
    if not reasons:  # tổ hợp điều kiện cùng lúc không phòng nào thoả
        reasons.append(
            Violation(
                ViolationCode.ROOM_CAPACITY,
                f"Không phòng nào (trong {n}) thoả đồng thời sức chứa, loại phòng và thiết bị",
            )
        )
    return tuple(reasons)


def allocate(
    requests: Sequence[SessionRequest],
    rooms: Sequence[Room],
    existing: Sequence[Booking] = (),
) -> AllocationResult:
    """Xếp phòng tự động.

    `existing`: các buổi đã có phòng trong DB — engine coi là cố định, không đụng tới.
    """
    result = AllocationResult()
    bookings: list[Booking] = list(existing)

    valid: list[SessionRequest] = []
    for req in requests:
        errs = validate_request_data(req)
        if errs:
            result.invalid.append(Unplaced(req.session_id, req.class_code, tuple(errs)))
        else:
            valid.append(req)

    sorted_rooms = sorted(rooms, key=best_fit_key)

    for req in sorted(valid, key=difficulty_key):
        chosen: Room | None = None
        for room in sorted_rooms:  # đã sắp nhỏ -> lớn nên cái đầu tiên hợp lệ là best-fit
            if not validate_assignment(req, room, bookings):
                chosen = room
                break

        if chosen is None:
            result.unassigned.append(
                Unplaced(req.session_id, req.class_code, explain_failure(req, sorted_rooms, bookings))
            )
            continue

        bookings.append(
            Booking(
                session_id=req.session_id,
                room_id=chosen.id,
                weekday=req.weekday,
                start_time=req.start_time,
                end_time=req.end_time,
                lecturer=req.lecturer,
            )
        )
        result.assigned.append(
            Placement(
                session_id=req.session_id,
                class_code=req.class_code,
                room_id=chosen.id,
                room_code=chosen.code,
                wasted_seats=chosen.capacity - req.student_count,
            )
        )

    return result

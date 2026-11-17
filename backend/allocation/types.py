"""Kiểu dữ liệu thuần Python cho Auto Allocation Engine.

Engine KHÔNG phụ thuộc SQLAlchemy/FastAPI để có thể unit test độc lập.
Lớp router (allocation_router.py) chịu trách nhiệm chuyển ORM <-> các dataclass này.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import Enum


def parse_equipment(raw: str | None) -> frozenset[str]:
    """Chuẩn hoá chuỗi thiết bị 'Máy chiếu, Điều hòa' -> {'máy chiếu', 'điều hòa'}.

    Cùng quy tắc với main.py hiện tại (tách theo dấu phẩy, bỏ khoảng trắng, casefold).
    """
    if not raw:
        return frozenset()
    return frozenset(x.strip().casefold() for x in raw.split(",") if x.strip())


class ViolationCode(str, Enum):
    INVALID_DATA = "INVALID_DATA"
    ROOM_CAPACITY = "ROOM_CAPACITY"
    ROOM_TYPE = "ROOM_TYPE"
    ROOM_EQUIPMENT = "ROOM_EQUIPMENT"
    ROOM_TIME_CONFLICT = "ROOM_TIME_CONFLICT"
    LECTURER_TIME_CONFLICT = "LECTURER_TIME_CONFLICT"
    NO_ROOMS = "NO_ROOMS"


@dataclass(frozen=True)
class Violation:
    code: ViolationCode
    message: str


@dataclass(frozen=True)
class Room:
    id: int
    code: str
    capacity: int
    room_type: str = "classroom"
    equipment: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SessionRequest:
    """Một buổi học cần có phòng (tương ứng một dòng timetable_sessions)."""

    session_id: int
    class_code: str
    student_count: int
    weekday: int
    start_time: time
    end_time: time
    required_room_type: str = "classroom"
    required_equipment: frozenset[str] = frozenset()
    lecturer: str | None = None  # None = chưa có dữ liệu giảng viên -> bỏ qua ràng buộc
    course_name: str = ""


@dataclass(frozen=True)
class Booking:
    """Một buổi học ĐÃ có phòng (nguồn: DB hoặc kết quả đã xếp trong lượt chạy này)."""

    session_id: int
    room_id: int
    weekday: int
    start_time: time
    end_time: time
    lecturer: str | None = None


@dataclass(frozen=True)
class Placement:
    session_id: int
    class_code: str
    room_id: int
    room_code: str
    wasted_seats: int  # capacity - student_count, thước đo độ lãng phí


@dataclass(frozen=True)
class Unplaced:
    session_id: int
    class_code: str
    reasons: tuple[Violation, ...]


@dataclass
class AllocationResult:
    assigned: list[Placement] = field(default_factory=list)
    unassigned: list[Unplaced] = field(default_factory=list)
    invalid: list[Unplaced] = field(default_factory=list)

    @property
    def summary(self) -> dict:
        total = len(self.assigned) + len(self.unassigned) + len(self.invalid)
        wasted = sum(p.wasted_seats for p in self.assigned)
        return {
            "total": total,
            "assigned": len(self.assigned),
            "unassigned": len(self.unassigned),
            "invalid": len(self.invalid),
            "total_wasted_seats": wasted,
        }

"""API cho Auto Allocation Engine (Phan Quang Hoàng) - Đã tích hợp RBAC, BR-03 & Audit Log (Đặng Huy Hoàng).

- POST /api/allocation/run       : xếp tự động (mặc định chỉ xem trước, apply=true mới lưu DB)
- POST /api/allocation/validate  : kiểm tra một phép gán/đổi phòng thủ công bằng cùng hàm validate
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from allocation import (
    AllocationResult,
    Booking,
    Room as RoomDTO,
    SessionRequest,
    Unplaced,
    Violation,
    allocate,
    parse_equipment,
    validate_assignment,
)
from auth import (
    ROLE_ADMIN,
    ROLE_LECTURER,
    ROLE_OFFICER,
    User,
    require_role,
    write_audit_log,
)
from database import get_db
from models import CourseClass, Notification, Room, TimetableSession
from ops_router import check_first_closure

allocation_router = APIRouter(prefix="/api/allocation", tags=["Allocation"])


# ---------- Schemas ----------

class RunRequest(BaseModel):
    session_ids: list[int] | None = Field(
        default=None,
        description="Chỉ xếp các buổi này. Bỏ trống = tất cả buổi chưa có phòng.",
    )
    apply: bool = Field(
        default=False,
        description="false = chỉ xem trước (không ghi DB); true = lưu kết quả xếp được vào DB.",
    )


class ValidateRequest(BaseModel):
    session_id: int = Field(gt=0)
    room_id: int = Field(gt=0)


# ---------- Chuyển ORM -> DTO ----------

def _room_dto(r: Room) -> RoomDTO:
    return RoomDTO(r.id, r.room_code, r.capacity, r.room_type, parse_equipment(r.equipment))


def _request_dto(s: TimetableSession, c: CourseClass) -> SessionRequest:
    return SessionRequest(
        session_id=s.id,
        class_code=c.class_code,
        course_name=c.course_name,
        student_count=c.student_count,
        weekday=s.weekday,
        start_time=s.start_time,
        end_time=s.end_time,
        required_room_type=c.required_room_type,
        required_equipment=parse_equipment(c.required_equipment),
        lecturer=getattr(c, "lecturer", None),
    )


def _booking_dto(s: TimetableSession, c: CourseClass) -> Booking:
    return Booking(s.id, s.room_id, s.weekday, s.start_time, s.end_time, getattr(c, "lecturer", None))


def _violation_json(v: Violation) -> dict:
    return {"code": v.code.value, "message": v.message}


def _unplaced_json(u: Unplaced) -> dict:
    return {
        "session_id": u.session_id,
        "class_code": u.class_code,
        "reasons": [_violation_json(v) for v in u.reasons],
    }


def _result_json(res: AllocationResult, applied: bool) -> dict:
    return {
        "applied": applied,
        "summary": res.summary,
        "assigned": [
            {
                "session_id": p.session_id,
                "class_code": p.class_code,
                "room_id": p.room_id,
                "room_code": p.room_code,
                "wasted_seats": p.wasted_seats,
            }
            for p in res.assigned
        ],
        "unassigned": [_unplaced_json(u) for u in res.unassigned],
        "invalid": [_unplaced_json(u) for u in res.invalid],
    }


# ---------- Endpoints ----------

@allocation_router.post("/run")
def run_allocation(
    body: RunRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    body = body or RunRequest()

    if body.apply:
        check_first_closure(db)

    q = db.query(TimetableSession, CourseClass).join(
        CourseClass, CourseClass.id == TimetableSession.class_id
    )
    rows = q.all()

    if body.session_ids is not None:
        wanted = set(body.session_ids)
        missing = wanted - {s.id for s, _ in rows}
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy buổi học: {sorted(missing)}",
            )
        targets = [(s, c) for s, c in rows if s.id in wanted]
    else:
        targets = [(s, c) for s, c in rows if s.room_id is None]

    target_ids = {s.id for s, _ in targets}
    existing = [_booking_dto(s, c) for s, c in rows if s.room_id is not None and s.id not in target_ids]

    rooms = [_room_dto(r) for r in db.query(Room).all()]
    requests = [_request_dto(s, c) for s, c in targets]

    result = allocate(requests, rooms, existing)

    applied = False
    if body.apply and result.assigned:
        by_id = {s.id: s for s, _ in targets}
        for p in result.assigned:
            by_id[p.session_id].room_id = p.room_id

        write_audit_log(
            db,
            current_user,
            action="AUTO_ALLOCATE",
            target=f"{len(result.assigned)}/{result.summary['total']} buổi học",
            new_value=", ".join(f"{p.class_code}->{p.room_code}" for p in result.assigned[:6]),
            reason="Kích hoạt Auto Allocation Engine (Greedy Best-fit)",
        )
        db.add(
            Notification(
                target_role=None,
                category="Xếp phòng tự động",
                tone="g",
                message=(
                    f"Phòng Đào tạo vừa hoàn tất xếp phòng tự động cho "
                    f"{len(result.assigned)}/{result.summary['total']} buổi học."
                ),
            )
        )
        try:
            db.commit()
            applied = True
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Kết quả xếp vi phạm ràng buộc database")

    return _result_json(result, applied)


@allocation_router.post("/validate")
def validate_manual_assignment(
    body: ValidateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER, ROLE_LECTURER])),
):
    """Kiểm tra trước khi đổi phòng thủ công. Cùng `validate_assignment` với thuật toán tự động."""
    session = db.query(TimetableSession).filter(TimetableSession.id == body.session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học")
    course = db.query(CourseClass).filter(CourseClass.id == session.class_id).first()
    room = db.query(Room).filter(Room.id == body.room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")

    rows = (
        db.query(TimetableSession, CourseClass)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .filter(TimetableSession.room_id.isnot(None))
        .all()
    )
    bookings = [_booking_dto(s, c) for s, c in rows]

    violations = validate_assignment(
        _request_dto(session, course),
        _room_dto(room),
        bookings,
        ignore_session_id=session.id,
    )
    return {"valid": not violations, "violations": [_violation_json(v) for v in violations]}

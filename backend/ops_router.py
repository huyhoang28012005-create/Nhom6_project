"""
CAMS - Module Tích hợp Nghiệp vụ Sprint 2 & Sprint 3 (Đặng Huy Hoàng)
Bao gồm:
- Tra cứu Phòng trống & Tra cứu Thời khóa biểu theo MSSV / Giảng viên / Lớp (STU-01, STU-02, LEC-01, LEC-02)
- Thống kê & Báo cáo hiệu suất khai thác phòng học (Sprint 3 Analytics)
- Cấu hình Ca học & Mốc thời hạn Closure Dates (ADM-03, ADM-04, BR-03)
- Đơn xin đổi phòng & Phê duyệt tự động cập nhật TKB (LEC-03, LEC-04, OFF-07)
- Đặt phòng học nhóm, Báo cáo sự cố, Thông báo & Nhật ký kiểm toán Audit Log (ADM-05, BR-04, STU-03)
- Khởi tạo bộ dữ liệu mẫu chuẩn nghiệm thu (Seed Demo Data)
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from allocation import (
    Booking as AllocationBooking,
    Room as RoomDTO,
    SessionRequest,
    parse_equipment,
    times_overlap,
    validate_assignment,
    ViolationCode,
)
from auth import (
    ROLE_ADMIN,
    ROLE_LECTURER,
    ROLE_OFFICER,
    ROLE_STUDENT,
    User,
    ensure_demo_users,
    get_current_user,
    get_optional_user,
    require_role,
    write_audit_log,
)
from database import get_db
from excel_service import DEFAULT_SHIFT_TIMES
from models import (
    AuditLog,
    CourseClass,
    IssueReport,
    Notification,
    Room,
    RoomBooking,
    RoomChangeRequest,
    ShiftConfig,
    StudentEnrollment,
    SystemSetting,
    TimetableSession,
)

ops_router = APIRouter(prefix="/api", tags=["Integration, Lookup, Stats & Governance"])


WEEKDAY_LABELS = {
    1: "Thứ 2",
    2: "Thứ 3",
    3: "Thứ 4",
    4: "Thứ 5",
    5: "Thứ 6",
    6: "Thứ 7",
    7: "Chủ nhật",
}

STANDARD_SHIFTS = [
    (1, "Ca 1", "Tiết 1–3", time(7, 0), time(9, 30)),
    (2, "Ca 2", "Tiết 4–6", time(9, 45), time(12, 0)),
    (3, "Ca 3", "Tiết 7–9", time(13, 0), time(15, 30)),
    (4, "Ca 4", "Tiết 10–12", time(15, 45), time(18, 0)),
    (5, "Ca 5", "Tiết 13–15", time(18, 15), time(20, 15)),
    (6, "Ca 6", "Ca tối phụ", time(20, 20), time(21, 50)),
]


def infer_shift_number(start_t: time, end_t: time) -> Optional[int]:
    for num, _, _, s, e in STANDARD_SHIFTS:
        if times_overlap(start_t, end_t, s, e):
            return num
    return None


def ensure_settings_and_shifts(db: Session) -> SystemSetting:
    setting = db.query(SystemSetting).first()
    if not setting:
        setting = SystemSetting(
            semester_name="Học kỳ 1 · Năm học 2026–2027",
            first_closure_date="2026-12-15",
            final_closure_date="2026-12-31",
            enforce_closure=True,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    if db.query(ShiftConfig).count() == 0:
        for num, name, periods, s, e in STANDARD_SHIFTS:
            db.add(
                ShiftConfig(
                    shift_number=num,
                    shift_name=name,
                    period_range=periods,
                    start_time=s,
                    end_time=e,
                )
            )
        db.commit()

    return setting


def check_first_closure(db: Session) -> None:
    """BR-03: Quá First Closure Date -> Khóa tải file Excel TKB thô và tự động xếp phòng."""
    setting = ensure_settings_and_shifts(db)
    if not setting.enforce_closure:
        return
    try:
        first_dt = date.fromisoformat(setting.first_closure_date)
    except ValueError:
        return
    if date.today() > first_dt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Đã quá hạn First Closure Date ({setting.first_closure_date}). "
                "Chức năng nạp thời khóa biểu và tự động xếp phòng đã bị khóa (BR-03)."
            ),
        )


def check_final_closure(db: Session) -> None:
    """BR-03: Quá Final Closure Date -> Chế độ Read-only, khóa đổi phòng và đơn xin đổi phòng."""
    setting = ensure_settings_and_shifts(db)
    if not setting.enforce_closure:
        return
    try:
        final_dt = date.fromisoformat(setting.final_closure_date)
    except ValueError:
        return
    if date.today() > final_dt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Đã quá hạn Final Closure Date ({setting.final_closure_date}). "
                "Hệ thống đang ở chế độ Chỉ đọc (Read-only), không thể điều chỉnh hay đổi phòng (BR-03)."
            ),
        )


def serialize_enriched_session(
    s: TimetableSession,
    c: CourseClass,
    r: Optional[Room],
) -> dict[str, Any]:
    shift_no = infer_shift_number(s.start_time, s.end_time)
    overloaded = bool(r and c.student_count > r.capacity)
    wasted = (r.capacity - c.student_count) if (r and r.capacity >= c.student_count) else 0
    return {
        "id": s.id,
        "class_id": c.id,
        "class_code": c.class_code,
        "course_name": c.course_name,
        "lecturer": c.lecturer or "Chưa phân công",
        "student_count": c.student_count,
        "required_room_type": c.required_room_type,
        "required_equipment": c.required_equipment or "",
        "weekday": s.weekday,
        "weekday_label": WEEKDAY_LABELS.get(s.weekday, f"Thứ {s.weekday + 1}"),
        "start_time": s.start_time.strftime("%H:%M:%S"),
        "end_time": s.end_time.strftime("%H:%M:%S"),
        "time_range": f"{s.start_time.strftime('%H:%M')} – {s.end_time.strftime('%H:%M')}",
        "shift": shift_no,
        "shift_label": f"Ca {shift_no}" if shift_no else f"{s.start_time.strftime('%H:%M')}",
        "room_id": r.id if r else None,
        "room_code": r.room_code if r else None,
        "building": r.building if r else None,
        "room_capacity": r.capacity if r else None,
        "room_type": r.room_type if r else None,
        "room_equipment": r.equipment if r else None,
        "status": "OVERLOADED" if overloaded else ("ASSIGNED" if r else "UNASSIGNED"),
        "wasted_seats": wasted,
    }


# ==============================================================================
# 1. API TRA CỨU PHÒNG TRỐNG & THỜI KHÓA BIỂU (STU-01, STU-02, LEC-01, LEC-02)
# ==============================================================================

@ops_router.get("/lookup/available-rooms", summary="Tra cứu danh sách phòng học & trạng thái trống theo ca")
def lookup_available_rooms(
    weekday: int = Query(default=1, ge=1, le=7),
    shift: Optional[int] = Query(default=None, ge=1, le=9),
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    building: Optional[str] = Query(default=None),
    min_capacity: int = Query(default=1, ge=1),
    room_type: Optional[str] = Query(default=None),
    equipment: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    only_free: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    if start_time and end_time:
        q_start = time.fromisoformat(start_time)
        q_end = time.fromisoformat(end_time)
    elif shift and shift in DEFAULT_SHIFT_TIMES:
        s_str, e_str = DEFAULT_SHIFT_TIMES[shift]
        q_start = time.fromisoformat(s_str)
        q_end = time.fromisoformat(e_str)
    else:
        q_start = time(7, 0)
        q_end = time(9, 30)

    rooms_q = db.query(Room).filter(Room.capacity >= min_capacity)
    if building and building != "Tất cả":
        rooms_q = rooms_q.filter(Room.building.ilike(f"%{building.strip()}%"))
    if room_type and room_type != "Tất cả":
        rooms_q = rooms_q.filter(Room.room_type == room_type.strip())
    if q and q.strip():
        kw = f"%{q.strip()}%"
        rooms_q = rooms_q.filter((Room.room_code.ilike(kw)) | (Room.building.ilike(kw)) | (Room.notes.ilike(kw)))

    rooms = rooms_q.order_by(Room.room_code).all()
    day_sessions = (
        db.query(TimetableSession, CourseClass)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .filter(TimetableSession.weekday == weekday, TimetableSession.room_id.isnot(None))
        .all()
    )

    req_eq = parse_equipment(equipment)
    items: list[dict[str, Any]] = []

    for r in rooms:
        room_eq = parse_equipment(r.equipment)
        if req_eq and not req_eq.issubset(room_eq):
            continue

        r_sessions = [(s, c) for s, c in day_sessions if s.room_id == r.id]
        busy_shifts = sorted(
            {
                sh
                for s, _ in r_sessions
                if (sh := infer_shift_number(s.start_time, s.end_time)) is not None
            }
        )
        occupying = next(
            (
                c.class_code
                for s, c in r_sessions
                if times_overlap(q_start, q_end, s.start_time, s.end_time)
            ),
            None,
        )
        is_free = occupying is None
        if only_free and not is_free:
            continue

        items.append(
            {
                "id": r.id,
                "room_code": r.room_code,
                "building": r.building,
                "floor": r.floor,
                "capacity": r.capacity,
                "room_type": r.room_type,
                "equipment": r.equipment or "",
                "equipment_list": sorted(room_eq),
                "notes": r.notes or "",
                "is_available": is_free,
                "occupying_class": occupying,
                "busy_shifts": busy_shifts,
            }
        )

    return {
        "weekday": weekday,
        "weekday_label": WEEKDAY_LABELS.get(weekday, ""),
        "start_time": q_start.strftime("%H:%M:%S"),
        "end_time": q_end.strftime("%H:%M:%S"),
        "total": len(items),
        "available_count": sum(1 for x in items if x["is_available"]),
        "rooms": items,
    }


@ops_router.get("/lookup/timetable", summary="Tra cứu lịch học theo MSSV, giảng viên, lớp, môn, phòng (STU-01, LEC-01)")
def lookup_timetable(
    student_code: Optional[str] = Query(default=None, description="MSSV để tra cứu lịch cá nhân (STU-01)"),
    lecturer: Optional[str] = Query(default=None),
    class_code: Optional[str] = Query(default=None),
    weekday: Optional[int] = Query(default=None, ge=1, le=7),
    building: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    student_info: Optional[dict[str, Any]] = None
    enrolled_class_ids: Optional[set[int]] = None

    if student_code and student_code.strip():
        code_clean = student_code.strip()
        enrollments = (
            db.query(StudentEnrollment)
            .filter(StudentEnrollment.student_code.ilike(code_clean))
            .all()
        )
        if enrollments:
            first = enrollments[0]
            student_info = {
                "student_code": first.student_code,
                "student_name": first.student_name,
                "administrative_class": first.administrative_class,
                "department": first.department,
            }
            enrolled_class_ids = {e.class_id for e in enrollments}
        else:
            enrolled_class_ids = set()

    query = (
        db.query(TimetableSession, CourseClass, Room)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .outerjoin(Room, Room.id == TimetableSession.room_id)
    )

    if enrolled_class_ids is not None:
        if not enrolled_class_ids:
            return {"student": None, "total": 0, "sessions": []}
        query = query.filter(TimetableSession.class_id.in_(enrolled_class_ids))

    if lecturer and lecturer.strip():
        query = query.filter(CourseClass.lecturer.ilike(f"%{lecturer.strip()}%"))
    if class_code and class_code.strip():
        query = query.filter(CourseClass.class_code.ilike(f"%{class_code.strip()}%"))
    if weekday is not None:
        query = query.filter(TimetableSession.weekday == weekday)
    if building and building != "Tất cả":
        query = query.filter(Room.building.ilike(f"%{building.strip()}%"))
    if q and q.strip():
        kw = f"%{q.strip()}%"
        # Nếu gõ đúng MSSV vào thanh tìm kiếm chung cũng tự nhận diện
        mssv_matches = (
            db.query(StudentEnrollment.class_id)
            .filter(StudentEnrollment.student_code.ilike(q.strip()))
            .all()
        )
        if mssv_matches:
            cids = [m[0] for m in mssv_matches]
            first_st = db.query(StudentEnrollment).filter(StudentEnrollment.student_code.ilike(q.strip())).first()
            if first_st:
                student_info = {
                    "student_code": first_st.student_code,
                    "student_name": first_st.student_name,
                    "administrative_class": first_st.administrative_class,
                    "department": first_st.department,
                }
            query = query.filter(TimetableSession.class_id.in_(cids))
        else:
            query = query.filter(
                (CourseClass.class_code.ilike(kw))
                | (CourseClass.course_name.ilike(kw))
                | (CourseClass.lecturer.ilike(kw))
                | (Room.room_code.ilike(kw))
            )

    rows = query.order_by(TimetableSession.weekday, TimetableSession.start_time).all()
    sessions = [serialize_enriched_session(s, c, r) for s, c, r in rows]
    return {
        "student": student_info,
        "total": len(sessions),
        "sessions": sessions,
    }


# ==============================================================================
# 2. API THỐNG KÊ & DASHBOARD HIỆU SUẤT PHÒNG HỌC (SPRINT 3 - TUẦN 5)
# ==============================================================================

@ops_router.get("/stats/overview", summary="Thống kê tổng quan & tỷ lệ khai thác phòng học")
def get_statistics_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    rooms = db.query(Room).order_by(Room.room_code).all()
    classes = db.query(CourseClass).all()
    session_rows = (
        db.query(TimetableSession, CourseClass, Room)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .outerjoin(Room, Room.id == TimetableSession.room_id)
        .all()
    )

    total_rooms = len(rooms)
    total_classes = len(classes)
    total_sessions = len(session_rows)
    assigned = [(s, c, r) for s, c, r in session_rows if r is not None]
    unassigned_count = total_sessions - len(assigned)
    overloaded_count = sum(1 for _, c, r in assigned if r and c.student_count > r.capacity)
    total_wasted_seats = sum(max(0, r.capacity - c.student_count) for _, c, r in assigned if r)

    # Mỗi phòng có 36 ca tiêu chuẩn/tuần (6 ngày Thứ 2-Thứ 7 × 6 ca/ngày)
    weekly_slots_per_room = 36
    by_room: list[dict[str, Any]] = []
    building_agg: dict[str, dict[str, Any]] = {}

    for r in rooms:
        r_assigned = [(s, c) for s, c, rm in assigned if rm and rm.id == r.id]
        used_slots = len(r_assigned)
        util_pct = round(min(100.0, (used_slots / weekly_slots_per_room) * 100), 1)
        wasted = sum(max(0, r.capacity - c.student_count) for _, c in r_assigned)
        avg_fill = (
            round(sum(min(1.0, c.student_count / r.capacity) for _, c in r_assigned) / used_slots * 100, 1)
            if used_slots > 0
            else 0.0
        )
        by_room.append(
            {
                "room_id": r.id,
                "room_code": r.room_code,
                "building": r.building,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "sessions_count": used_slots,
                "utilization_pct": util_pct,
                "seat_fill_pct": avg_fill,
                "wasted_seats": wasted,
            }
        )

        b = building_agg.setdefault(
            r.building,
            {"building": r.building, "room_count": 0, "sessions_count": 0, "total_capacity": 0},
        )
        b["room_count"] += 1
        b["sessions_count"] += used_slots
        b["total_capacity"] += r.capacity

    by_building = []
    for b in building_agg.values():
        max_slots = b["room_count"] * weekly_slots_per_room
        b["utilization_pct"] = round((b["sessions_count"] / max_slots) * 100, 1) if max_slots else 0.0
        by_building.append(b)

    by_weekday = []
    for wd in range(1, 7):
        wd_total = sum(1 for s, _, _ in session_rows if s.weekday == wd)
        wd_assigned = sum(1 for s, _, r in assigned if s.weekday == wd)
        by_weekday.append(
            {
                "weekday": wd,
                "label": WEEKDAY_LABELS[wd],
                "total_sessions": wd_total,
                "assigned_sessions": wd_assigned,
            }
        )

    pending_changes = db.query(RoomChangeRequest).filter(RoomChangeRequest.status == "PENDING").count()
    pending_bookings = db.query(RoomBooking).filter(RoomBooking.status == "PENDING").count()
    open_issues = db.query(IssueReport).filter(IssueReport.status != "RESOLVED").count()

    avg_util = (
        round((len(assigned) / (total_rooms * weekly_slots_per_room)) * 100, 1)
        if total_rooms > 0
        else 0.0
    )

    return {
        "total_rooms": total_rooms,
        "total_classes": total_classes,
        "total_sessions": total_sessions,
        "assigned_sessions": len(assigned),
        "unassigned_sessions": unassigned_count,
        "assignment_rate": round((len(assigned) / total_sessions) * 100, 1) if total_sessions else 0.0,
        "overloaded_sessions": overloaded_count,
        "total_wasted_seats": total_wasted_seats,
        "average_utilization_pct": avg_util,
        "pending_change_requests": pending_changes,
        "pending_bookings": pending_bookings,
        "open_issues": open_issues,
        "by_room": sorted(by_room, key=lambda x: (-x["sessions_count"], x["room_code"])),
        "by_building": sorted(by_building, key=lambda x: x["building"]),
        "by_weekday": by_weekday,
    }


# ==============================================================================
# 3. CẤU HÌNH HỆ THỐNG, CA HỌC & CLOSURE DATES (ADM-03, ADM-04, BR-03)
# ==============================================================================

class SettingsUpdateRequest(BaseModel):
    semester_name: Optional[str] = None
    first_closure_date: str
    final_closure_date: str
    enforce_closure: bool = True


@ops_router.get("/settings", summary="Xem cấu hình học kỳ, ca học & mốc Closure Dates")
def get_system_settings(db: Session = Depends(get_db)):
    setting = ensure_settings_and_shifts(db)
    shifts = db.query(ShiftConfig).order_by(ShiftConfig.shift_number).all()
    today = date.today()
    first_dt = date.fromisoformat(setting.first_closure_date)
    final_dt = date.fromisoformat(setting.final_closure_date)

    return {
        "semester_name": setting.semester_name,
        "first_closure_date": setting.first_closure_date,
        "final_closure_date": setting.final_closure_date,
        "enforce_closure": setting.enforce_closure,
        "today": today.isoformat(),
        "is_past_first_closure": bool(setting.enforce_closure and today > first_dt),
        "is_past_final_closure": bool(setting.enforce_closure and today > final_dt),
        "days_until_first_closure": (first_dt - today).days,
        "days_until_final_closure": (final_dt - today).days,
        "shifts": [
            {
                "shift_number": sh.shift_number,
                "shift_name": sh.shift_name,
                "period_range": sh.period_range,
                "start_time": sh.start_time.strftime("%H:%M"),
                "end_time": sh.end_time.strftime("%H:%M"),
            }
            for sh in shifts
        ],
    }


@ops_router.put("/settings", summary="Cập nhật mốc First/Final Closure Date (ADM-04)")
def update_system_settings(
    body: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    try:
        first_dt = date.fromisoformat(body.first_closure_date)
        final_dt = date.fromisoformat(body.final_closure_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Định dạng ngày phải là YYYY-MM-DD")

    if final_dt <= first_dt:
        raise HTTPException(
            status_code=422,
            detail="Ràng buộc ADM-04: Final Closure Date bắt buộc phải sau First Closure Date",
        )

    setting = ensure_settings_and_shifts(db)
    old_val = f"First={setting.first_closure_date}, Final={setting.final_closure_date}, Enforce={setting.enforce_closure}"
    if body.semester_name:
        setting.semester_name = body.semester_name.strip()
    setting.first_closure_date = body.first_closure_date
    setting.final_closure_date = body.final_closure_date
    setting.enforce_closure = body.enforce_closure

    write_audit_log(
        db,
        current_user,
        action="UPDATE_CLOSURE_SETTINGS",
        target="SystemSetting",
        old_value=old_val,
        new_value=f"First={setting.first_closure_date}, Final={setting.final_closure_date}, Enforce={setting.enforce_closure}",
        reason="Cập nhật cấu hình thời hạn đóng hệ thống",
    )
    db.commit()
    return get_system_settings(db)


# ==============================================================================
# 4. ĐƠN XIN ĐỔI PHÒNG CỦA GIẢNG VIÊN & PHÊ DUYỆT (LEC-03, LEC-04, OFF-07)
# ==============================================================================

class ChangeRequestCreate(BaseModel):
    session_id: int = Field(gt=0)
    requested_room_id: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=500)


class ReviewDecision(BaseModel):
    action: str = Field(pattern="^(APPROVE|REJECT)$")
    reject_reason: Optional[str] = None
    allow_overload: bool = False


@ops_router.get("/change-requests", summary="Danh sách đơn xin đổi phòng")
def list_change_requests(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    q = db.query(RoomChangeRequest).order_by(RoomChangeRequest.created_at.desc(), RoomChangeRequest.id.desc())
    if status_filter and status_filter != "ALL":
        q = q.filter(RoomChangeRequest.status == status_filter.upper())
    if current_user and current_user.role == ROLE_LECTURER:
        q = q.filter(
            (RoomChangeRequest.requester_username == current_user.username)
            | (RoomChangeRequest.lecturer_name.ilike(f"%{current_user.full_name}%"))
        )

    reqs = q.all()
    rooms_map = {r.id: r for r in db.query(Room).all()}
    sessions_map = {
        s.id: (s, c)
        for s, c in db.query(TimetableSession, CourseClass)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .all()
    }

    result = []
    for item in reqs:
        sc = sessions_map.get(item.session_id)
        old_r = rooms_map.get(item.old_room_id) if item.old_room_id else None
        new_r = rooms_map.get(item.requested_room_id)
        s_obj, c_obj = sc if sc else (None, None)
        result.append(
            {
                "id": item.id,
                "session_id": item.session_id,
                "class_code": c_obj.class_code if c_obj else f"#{item.session_id}",
                "course_name": c_obj.course_name if c_obj else "",
                "student_count": c_obj.student_count if c_obj else 0,
                "weekday": s_obj.weekday if s_obj else 1,
                "weekday_label": WEEKDAY_LABELS.get(s_obj.weekday, "") if s_obj else "",
                "time_range": f"{s_obj.start_time.strftime('%H:%M')} – {s_obj.end_time.strftime('%H:%M')}" if s_obj else "",
                "lecturer_name": item.lecturer_name,
                "old_room_id": item.old_room_id,
                "old_room_code": old_r.room_code if old_r else "Chưa gán",
                "requested_room_id": item.requested_room_id,
                "requested_room_code": new_r.room_code if new_r else "?",
                "requested_room_capacity": new_r.capacity if new_r else 0,
                "reason": item.reason,
                "status": item.status,
                "reject_reason": item.reject_reason,
                "reviewed_by": item.reviewed_by,
                "created_at": item.created_at.strftime("%d/%m/%Y %H:%M") if item.created_at else "",
            }
        )
    return result


@ops_router.post(
    "/change-requests",
    status_code=status.HTTP_201_CREATED,
    summary="Giảng viên gửi đơn xin đổi phòng (LEC-03)",
)
def create_change_request(
    body: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_LECTURER, ROLE_OFFICER, ROLE_ADMIN])),
):
    check_final_closure(db)

    session = db.query(TimetableSession).filter(TimetableSession.id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học")
    course = db.query(CourseClass).filter(CourseClass.id == session.class_id).first()
    new_room = db.query(Room).filter(Room.id == body.requested_room_id).first()
    if not new_room:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học đề nghị")
    if session.room_id == new_room.id:
        raise HTTPException(status_code=409, detail="Phòng đề nghị trùng với phòng hiện tại của lớp")

    conflict = (
        db.query(TimetableSession)
        .filter(
            TimetableSession.id != session.id,
            TimetableSession.room_id == new_room.id,
            TimetableSession.weekday == session.weekday,
            TimetableSession.start_time < session.end_time,
            TimetableSession.end_time > session.start_time,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Xung đột BR-01: Phòng {new_room.room_code} đã có lịch vào khung giờ này",
        )

    req = RoomChangeRequest(
        session_id=session.id,
        lecturer_name=course.lecturer or current_user.full_name,
        requester_username=current_user.username,
        old_room_id=session.room_id,
        requested_room_id=new_room.id,
        reason=body.reason.strip(),
        status="PENDING",
    )
    db.add(req)
    write_audit_log(
        db,
        current_user,
        action="CREATE_CHANGE_REQUEST",
        target=f"{course.class_code} (Session #{session.id})",
        old_value=str(session.room_id or "None"),
        new_value=new_room.room_code,
        reason=body.reason.strip(),
    )
    db.commit()
    db.refresh(req)
    return {"message": "Đã gửi đơn xin đổi phòng, đang chờ Phòng Đào tạo xét duyệt", "id": req.id}


@ops_router.post(
    "/change-requests/{req_id}/review",
    summary="Cán bộ Đào tạo duyệt / từ chối đơn đổi phòng (OFF-07)",
)
def review_change_request(
    req_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    officer: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    check_final_closure(db)

    req = db.query(RoomChangeRequest).filter(RoomChangeRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn xin đổi phòng")
    if req.status != "PENDING":
        raise HTTPException(status_code=409, detail="Đơn này đã được xử lý trước đó")

    session = db.query(TimetableSession).filter(TimetableSession.id == req.session_id).first()
    course = db.query(CourseClass).filter(CourseClass.id == session.class_id).first() if session else None
    old_room = db.query(Room).filter(Room.id == req.old_room_id).first() if req.old_room_id else None
    new_room = db.query(Room).filter(Room.id == req.requested_room_id).first()

    if body.action == "REJECT":
        if not body.reject_reason or not body.reject_reason.strip():
            raise HTTPException(status_code=422, detail="Bắt buộc nhập lý do từ chối đơn (OFF-07)")
        req.status = "REJECTED"
        req.reject_reason = body.reject_reason.strip()
        req.reviewed_by = officer.full_name
        req.reviewed_at = datetime.now(timezone.utc)

        db.add(
            Notification(
                target_username=req.requester_username,
                category="Kết quả duyệt",
                tone="r",
                message=(
                    f"Đơn xin đổi phòng lớp {course.class_code if course else ''} sang "
                    f"{new_room.room_code if new_room else ''} đã bị từ chối: {req.reject_reason}"
                ),
            )
        )
        write_audit_log(
            db,
            officer,
            action="REJECT_CHANGE_REQUEST",
            target=f"Request #{req.id} ({course.class_code if course else ''})",
            old_value=old_room.room_code if old_room else "Chưa gán",
            new_value=new_room.room_code if new_room else "",
            reason=req.reject_reason,
        )
        db.commit()
        return {"message": "Đã từ chối đơn đổi phòng", "status": "REJECTED"}

    # APPROVE -> Kiểm tra xung đột bằng bộ validate chung trước khi cập nhật TKB
    if not session or not course or not new_room:
        raise HTTPException(status_code=404, detail="Dữ liệu buổi học hoặc phòng không còn tồn tại")

    all_booked = (
        db.query(TimetableSession, CourseClass)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .filter(TimetableSession.room_id.isnot(None))
        .all()
    )
    bookings = [
        AllocationBooking(s.id, s.room_id, s.weekday, s.start_time, s.end_time, c.lecturer)
        for s, c in all_booked
    ]
    s_req = SessionRequest(
        session_id=session.id,
        class_code=course.class_code,
        course_name=course.course_name,
        student_count=course.student_count,
        weekday=session.weekday,
        start_time=session.start_time,
        end_time=session.end_time,
        required_room_type=course.required_room_type,
        required_equipment=parse_equipment(course.required_equipment),
        lecturer=course.lecturer,
    )
    r_dto = RoomDTO(
        new_room.id,
        new_room.room_code,
        new_room.capacity,
        new_room.room_type,
        parse_equipment(new_room.equipment),
    )
    violations = validate_assignment(s_req, r_dto, bookings, ignore_session_id=session.id)
    hard_codes = {ViolationCode.ROOM_TIME_CONFLICT, ViolationCode.LECTURER_TIME_CONFLICT, ViolationCode.INVALID_DATA}
    hard_v = [v for v in violations if v.code in hard_codes]
    if hard_v:
        raise HTTPException(status_code=409, detail=hard_v[0].message)
    if violations and not body.allow_overload:
        # Cho phép duyệt nếu chỉ khác loại phòng/thiết bị nhẹ? Nếu quá tải sức chứa báo rõ
        cap_v = [v for v in violations if v.code == ViolationCode.ROOM_CAPACITY]
        if cap_v:
            raise HTTPException(status_code=409, detail=cap_v[0].message)

    old_code = old_room.room_code if old_room else "Chưa gán"
    session.room_id = new_room.id
    req.status = "APPROVED"
    req.reviewed_by = officer.full_name
    req.reviewed_at = datetime.now(timezone.utc)

    db.add(
        Notification(
            target_role=None,
            category="Đổi phòng",
            tone="b",
            message=(
                f"Môn {course.course_name} ({course.class_code}) chuyển từ phòng "
                f"{old_code} sang {new_room.room_code} ({WEEKDAY_LABELS.get(session.weekday, '')})."
            ),
        )
    )
    write_audit_log(
        db,
        officer,
        action="APPROVE_CHANGE_REQUEST",
        target=f"{course.class_code} (Session #{session.id})",
        old_value=old_code,
        new_value=new_room.room_code,
        reason=req.reason,
    )
    db.commit()
    return {"message": f"Đã duyệt và cập nhật phòng {new_room.room_code}", "status": "APPROVED"}


# ==============================================================================
# 5. ĐẶT PHÒNG HỌC NHÓM, BÁO CÁO SỰ CỐ, THÔNG BÁO & AUDIT LOG (ADM-05 / BR-04)
# ==============================================================================

class RoomBookingCreate(BaseModel):
    room_id: int = Field(gt=0)
    use_date: str = Field(min_length=4, max_length=20)
    shift_label: str = Field(min_length=2, max_length=50)
    attendee_count: int = Field(gt=0)
    purpose: str = Field(min_length=10, max_length=500)


class IssueReportCreate(BaseModel):
    room_id: Optional[int] = None
    room_name: str = Field(min_length=1, max_length=100)
    issue_type: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=1000)


class IssueStatusUpdate(BaseModel):
    status: str = Field(pattern="^(RECEIVED|IN_PROGRESS|RESOLVED)$")


@ops_router.get("/bookings", summary="Lịch sử đặt/mượn phòng học")
def list_bookings(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    q = db.query(RoomBooking, Room).join(Room, Room.id == RoomBooking.room_id)
    if current_user and current_user.role in (ROLE_STUDENT, ROLE_LECTURER):
        q = q.filter(RoomBooking.requester_username == current_user.username)
    rows = q.order_by(RoomBooking.created_at.desc(), RoomBooking.id.desc()).all()
    return [
        {
            "id": b.id,
            "room_id": r.id,
            "room_code": r.room_code,
            "room_label": f"{r.room_code} ({r.building})",
            "requester_name": b.requester_name,
            "use_date": b.use_date,
            "shift_label": b.shift_label,
            "attendee_count": b.attendee_count,
            "purpose": b.purpose,
            "status": b.status,
        }
        for b, r in rows
    ]


@ops_router.post("/bookings", status_code=status.HTTP_201_CREATED, summary="Gửi yêu cầu đặt/mượn phòng")
def create_booking(
    body: RoomBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_final_closure(db)
    room = db.query(Room).filter(Room.id == body.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")
    if body.attendee_count > room.capacity:
        raise HTTPException(
            status_code=409,
            detail=f"Số người ({body.attendee_count}) vượt quá sức chứa phòng {room.room_code} ({room.capacity})",
        )

    conflict = (
        db.query(RoomBooking)
        .filter(
            RoomBooking.room_id == room.id,
            RoomBooking.use_date == body.use_date,
            RoomBooking.shift_label == body.shift_label,
            RoomBooking.status.in_(["PENDING", "APPROVED"]),
        )
        .first()
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Phòng này đã có người đặt trong cùng ngày và ca")

    booking = RoomBooking(
        room_id=room.id,
        requester_username=current_user.username,
        requester_name=current_user.full_name,
        use_date=body.use_date,
        shift_label=body.shift_label,
        attendee_count=body.attendee_count,
        purpose=body.purpose.strip(),
        status="PENDING",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"message": "Đã gửi yêu cầu đặt phòng, chờ duyệt", "id": booking.id}


@ops_router.post("/bookings/{booking_id}/cancel", summary="Hủy yêu cầu đặt phòng")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt đặt phòng")
    if current_user.role not in (ROLE_ADMIN, ROLE_OFFICER) and booking.requester_username != current_user.username:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hủy lượt đặt phòng này")
    booking.status = "CANCELLED"
    db.commit()
    return {"message": "Đã hủy đặt phòng thành công"}


@ops_router.post("/bookings/{booking_id}/review", summary="Duyệt / Từ chối mượn phòng")
def review_booking(
    booking_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    officer: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt đặt phòng")
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    booking.status = "APPROVED" if body.action == "APPROVE" else "REJECTED"
    db.add(
        Notification(
            target_username=booking.requester_username,
            category="Kết quả duyệt",
            tone="g" if booking.status == "APPROVED" else "r",
            message=(
                f"Yêu cầu đặt phòng {room.room_code if room else ''} ngày {booking.use_date} ({booking.shift_label}) "
                f"đã {'được duyệt' if booking.status == 'APPROVED' else 'bị từ chối'}."
            ),
        )
    )
    write_audit_log(
        db,
        officer,
        action=f"{body.action}_BOOKING",
        target=f"Booking #{booking.id} ({room.room_code if room else ''})",
        new_value=booking.status,
    )
    db.commit()
    return {"message": "Đã cập nhật trạng thái đặt phòng", "status": booking.status}


@ops_router.get("/issues", summary="Danh sách báo cáo sự cố phòng học")
def list_issues(db: Session = Depends(get_db)):
    rows = db.query(IssueReport).order_by(IssueReport.created_at.desc(), IssueReport.id.desc()).all()
    return [
        {
            "id": x.id,
            "room_id": x.room_id,
            "room_name": x.room_name,
            "reporter_name": x.reporter_name,
            "issue_type": x.issue_type,
            "description": x.description,
            "status": x.status,
            "created_at": x.created_at.strftime("%d/%m/%Y %H:%M") if x.created_at else "",
        }
        for x in rows
    ]


@ops_router.post("/issues", status_code=status.HTTP_201_CREATED, summary="Gửi báo cáo sự cố thiết bị/phòng")
def create_issue(
    body: IssueReportCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    issue = IssueReport(
        room_id=body.room_id,
        room_name=body.room_name.strip(),
        reporter_name=current_user.full_name if current_user else "Sinh viên",
        issue_type=body.issue_type.strip(),
        description=body.description.strip(),
        status="RECEIVED",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return {"message": "Đã gửi báo cáo sự cố thành công", "id": issue.id}


@ops_router.patch("/issues/{issue_id}", summary="Cập nhật tiến độ xử lý sự cố")
def update_issue_status(
    issue_id: int,
    body: IssueStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    issue = db.query(IssueReport).filter(IssueReport.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo sự cố")
    issue.status = body.status
    db.commit()
    return {"message": "Đã cập nhật trạng thái sự cố", "status": issue.status}


@ops_router.get("/notifications", summary="Xem danh sách thông báo (STU-03, LEC-04)")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    q = db.query(Notification)
    if current_user:
        q = q.filter(
            (Notification.target_username.is_(None) & Notification.target_role.is_(None))
            | (Notification.target_role == current_user.role)
            | (Notification.target_username == current_user.username)
        )
    rows = q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(30).all()
    return [
        {
            "id": n.id,
            "category": n.category,
            "tone": n.tone,
            "message": n.message,
            "is_unread": n.is_unread,
            "created_at": n.created_at.strftime("%d/%m/%Y %H:%M") if n.created_at else "",
        }
        for n in rows
    ]


@ops_router.post("/notifications/read-all", summary="Đánh dấu đã đọc tất cả thông báo")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_unread == True).update({"is_unread": False})
    db.commit()
    return {"message": "Đã đánh dấu đã đọc"}


@ops_router.get("/audit-logs", summary="Xem Nhật ký kiểm toán hệ thống bất biến (ADM-05, BR-04)")
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": lg.id,
            "actor_name": lg.actor_name,
            "actor_role": lg.actor_role,
            "action": lg.action,
            "target": lg.target,
            "old_value": lg.old_value or "—",
            "new_value": lg.new_value or "—",
            "reason": lg.reason or "",
            "created_at": lg.created_at.strftime("%d/%m/%Y %H:%M:%S") if lg.created_at else "",
        }
        for lg in logs
    ]


# ==============================================================================
# 6. KHỞI TẠO BỘ DỮ LIỆU MẪU CHUẨN NGHIỆM THU SPRINT 2 & SPRINT 3
# ==============================================================================

def seed_demo_dataset(db: Session, reset: bool = False) -> dict[str, Any]:
    ensure_settings_and_shifts(db)
    ensure_demo_users(db)

    if reset:
        db.query(RoomChangeRequest).delete()
        db.query(RoomBooking).delete()
        db.query(StudentEnrollment).delete()
        db.query(TimetableSession).delete()
        db.query(CourseClass).delete()
        db.query(IssueReport).delete()
        db.query(Room).delete()
        db.commit()

    if db.query(Room).count() > 0:
        return {
            "seeded": False,
            "rooms": db.query(Room).count(),
            "classes": db.query(CourseClass).count(),
            "sessions": db.query(TimetableSession).count(),
        }

    demo_rooms = [
        Room(room_code="A2-305", building="Tòa A2", floor=3, capacity=200, room_type="hall", equipment="Máy chiếu, Điều hòa, Micro, Loa, Wi-Fi, Ổ cắm", notes="Giảng đường bậc thang lớn"),
        Room(room_code="B2-110", building="Tòa B2", floor=1, capacity=120, room_type="hall", equipment="Máy chiếu, Điều hòa, Micro, Loa, Wi-Fi", notes="Giảng đường tiêu chuẩn"),
        Room(room_code="A1-402", building="Tòa A1", floor=4, capacity=70, room_type="classroom", equipment="Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng lý thuyết 70 chỗ"),
        Room(room_code="B1-204", building="Tòa B1", floor=2, capacity=60, room_type="classroom", equipment="Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng học tiêu chuẩn"),
        Room(room_code="B1-205", building="Tòa B1", floor=2, capacity=50, room_type="classroom", equipment="Máy chiếu, Điều hòa, Wi-Fi", notes="Phòng học tiêu chuẩn"),
        Room(room_code="A1-201", building="Tòa A1", floor=2, capacity=45, room_type="classroom", equipment="Máy chiếu, Điều hòa, Wi-Fi", notes="Phòng học vừa"),
        Room(room_code="A1-202", building="Tòa A1", floor=2, capacity=35, room_type="classroom", equipment="Điều hòa, Wi-Fi", notes="Phòng ngoại ngữ / thảo luận"),
        Room(room_code="C3-101", building="Tòa C3", floor=1, capacity=45, room_type="lab", equipment="Máy tính, Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng Lab mạng & lập trình"),
        Room(room_code="C3-102", building="Tòa C3", floor=1, capacity=50, room_type="lab", equipment="Máy tính, Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng Lab CSDL & AI"),
        Room(room_code="TV-12", building="Thư viện", floor=2, capacity=15, room_type="group", equipment="Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng học nhóm sinh viên"),
        Room(room_code="TV-301", building="Thư viện", floor=3, capacity=30, room_type="classroom", equipment="Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", notes="Phòng chuyên đề thư viện"),
    ]
    db.add_all(demo_rooms)
    db.flush()
    rm = {r.room_code: r for r in demo_rooms}

    demo_classes = [
        CourseClass(class_code="INT2211-02", course_name="Cơ sở dữ liệu", lecturer="TS. Nguyễn Văn An", student_count=58, required_room_type="classroom", required_equipment="Máy chiếu, Điều hòa"),
        CourseClass(class_code="MAT1101-05", course_name="Giải tích 2", lecturer="PGS. Trần Thị Mai", student_count=95, required_room_type="hall", required_equipment="Máy chiếu, Micro"),
        CourseClass(class_code="INT3304-01", course_name="Thực hành Mạng máy tính", lecturer="ThS. Lê Hoàng Nam", student_count=40, required_room_type="lab", required_equipment="Máy tính, Máy chiếu"),
        CourseClass(class_code="ENG1001-03", course_name="Tiếng Anh học thuật 1", lecturer="ThS. Phạm Thu Hà", student_count=32, required_room_type="classroom", required_equipment="Điều hòa"),
        CourseClass(class_code="INT3401-01", course_name="Trí tuệ nhân tạo", lecturer="TS. Nguyễn Văn An", student_count=65, required_room_type="classroom", required_equipment="Máy chiếu, Điều hòa"),
        CourseClass(class_code="INT2204-01", course_name="Lập trình hướng đối tượng", lecturer="TS. Vũ Đức Minh", student_count=48, required_room_type="classroom", required_equipment="Máy chiếu"),
        CourseClass(class_code="INT2204-LAB", course_name="Thực hành OOP", lecturer="TS. Vũ Đức Minh", student_count=44, required_room_type="lab", required_equipment="Máy tính, Máy chiếu"),
        CourseClass(class_code="PHY1100-01", course_name="Vật lý đại cương", lecturer="PGS. Hoàng Quốc Bảo", student_count=150, required_room_type="hall", required_equipment="Máy chiếu, Micro, Loa"),
        CourseClass(class_code="INT3110-02", course_name="Đảm bảo chất lượng phần mềm", lecturer="TS. Đỗ Minh Tuấn", student_count=42, required_room_type="classroom", required_equipment="Máy chiếu, Điều hòa"),
        CourseClass(class_code="INT3507-01", course_name="Phát triển ứng dụng Web", lecturer="ThS. Lê Hoàng Nam", student_count=46, required_room_type="lab", required_equipment="Máy tính, Máy chiếu"),
        CourseClass(class_code="STA2001-01", course_name="Xác suất thống kê", lecturer="PGS. Trần Thị Mai", student_count=55, required_room_type="classroom", required_equipment="Máy chiếu"),
        CourseClass(class_code="POL1001-04", course_name="Triết học Mác - Lênin", lecturer="TS. Ngô Thanh Tùng", student_count=180, required_room_type="hall", required_equipment="Máy chiếu, Micro"),
    ]
    db.add_all(demo_classes)
    db.flush()
    cm = {c.class_code: c for c in demo_classes}

    # Một phần buổi học đã có phòng, một phần để trống (room_id=None) để demo Auto Allocation Engine!
    demo_sessions = [
        # Đã gán phòng sẵn
        TimetableSession(class_id=cm["INT2211-02"].id, weekday=1, start_time=time(7, 0), end_time=time(9, 30), room_id=rm["B1-204"].id),
        TimetableSession(class_id=cm["MAT1101-05"].id, weekday=1, start_time=time(9, 45), end_time=time(12, 0), room_id=rm["B2-110"].id),
        TimetableSession(class_id=cm["INT3304-01"].id, weekday=1, start_time=time(13, 0), end_time=time(15, 30), room_id=rm["C3-101"].id),
        TimetableSession(class_id=cm["PHY1100-01"].id, weekday=2, start_time=time(7, 0), end_time=time(9, 30), room_id=rm["A2-305"].id),
        TimetableSession(class_id=cm["INT3110-02"].id, weekday=3, start_time=time(7, 0), end_time=time(9, 30), room_id=rm["A1-201"].id),
        TimetableSession(class_id=cm["ENG1001-03"].id, weekday=4, start_time=time(9, 45), end_time=time(12, 0), room_id=rm["A1-202"].id),
        # Chờ tự động xếp phòng (room_id=None)
        TimetableSession(class_id=cm["INT3401-01"].id, weekday=2, start_time=time(9, 45), end_time=time(12, 0), room_id=None),
        TimetableSession(class_id=cm["INT2204-01"].id, weekday=2, start_time=time(13, 0), end_time=time(15, 30), room_id=None),
        TimetableSession(class_id=cm["INT2204-LAB"].id, weekday=3, start_time=time(13, 0), end_time=time(15, 30), room_id=None),
        TimetableSession(class_id=cm["INT3507-01"].id, weekday=4, start_time=time(7, 0), end_time=time(9, 30), room_id=None),
        TimetableSession(class_id=cm["STA2001-01"].id, weekday=5, start_time=time(7, 0), end_time=time(9, 30), room_id=None),
        TimetableSession(class_id=cm["POL1001-04"].id, weekday=5, start_time=time(9, 45), end_time=time(12, 0), room_id=None),
        TimetableSession(class_id=cm["INT3110-02"].id, weekday=6, start_time=time(7, 0), end_time=time(9, 30), room_id=None),
        TimetableSession(class_id=cm["INT2211-02"].id, weekday=4, start_time=time(13, 0), end_time=time(15, 30), room_id=None),
    ]
    db.add_all(demo_sessions)
    db.flush()

    # Đăng ký học phần cho sinh viên demo (MSSV: 21021234 và SV001)
    for code in ["INT2211-02", "MAT1101-05", "INT3304-01", "INT3110-02", "INT3401-01"]:
        db.add(
            StudentEnrollment(
                student_code="21021234",
                student_name="Nguyễn Minh Anh",
                administrative_class="K66-CNTT2",
                department="Công nghệ thông tin",
                class_id=cm[code].id,
            )
        )
    for code in ["PHY1100-01", "ENG1001-03", "INT2204-01", "INT2204-LAB"]:
        db.add(
            StudentEnrollment(
                student_code="SV001",
                student_name="Trần Quốc Khánh",
                administrative_class="K67-CNTT1",
                department="Công nghệ thông tin",
                class_id=cm[code].id,
            )
        )

    # Đơn xin đổi phòng mẫu
    db.add_all(
        [
            RoomChangeRequest(
                session_id=demo_sessions[0].id,
                lecturer_name="TS. Nguyễn Văn An",
                requester_username="gv_an",
                old_room_id=rm["B1-204"].id,
                requested_room_id=rm["A1-402"].id,
                reason="Sĩ số lớp tăng thêm sinh viên đăng ký bổ sung, cần phòng rộng hơn.",
                status="PENDING",
            ),
            RoomChangeRequest(
                session_id=demo_sessions[1].id,
                lecturer_name="PGS. Trần Thị Mai",
                requester_username="gv_an",
                old_room_id=rm["B2-110"].id,
                requested_room_id=rm["A2-305"].id,
                reason="Micro không dây phòng B2-110 chập chờn, xin chuyển sang A2-305.",
                status="PENDING",
            ),
        ]
    )

    # Lịch sử mượn phòng học nhóm mẫu
    db.add_all(
        [
            RoomBooking(
                room_id=rm["TV-12"].id,
                requester_username="sv_minhanh",
                requester_name="Nguyễn Minh Anh",
                use_date="2026-11-27",
                shift_label="Ca 4 · 15:45",
                attendee_count=8,
                purpose="Họp nhóm Sprint 3 môn Đảm bảo chất lượng phần mềm",
                status="PENDING",
            ),
            RoomBooking(
                room_id=rm["TV-301"].id,
                requester_username="sv_minhanh",
                requester_name="Nguyễn Minh Anh",
                use_date="2026-11-20",
                shift_label="Ca 3 · 13:00",
                attendee_count=18,
                purpose="Ôn tập nhóm môn Cơ sở dữ liệu",
                status="APPROVED",
            ),
        ]
    )

    # Sự cố & thông báo mẫu
    db.add_all(
        [
            IssueReport(
                room_id=rm["A2-305"].id,
                room_name="A2-305 (Tòa A2)",
                reporter_name="TS. Nguyễn Văn An",
                issue_type="Thiết bị (máy chiếu, micro)",
                description="Cổng HDMI máy chiếu chính chập chờn khi kết nối laptop.",
                status="IN_PROGRESS",
            ),
            IssueReport(
                room_id=rm["B1-204"].id,
                room_name="B1-204 (Tòa B1)",
                reporter_name="Nguyễn Minh Anh",
                issue_type="Điều hòa / điện",
                description="Điều hòa cuối phòng phát tiếng kêu nhỏ khi bật 22 độ.",
                status="RESOLVED",
            ),
        ]
    )

    db.add_all(
        [
            Notification(
                target_role=None,
                category="Đổi phòng",
                tone="b",
                message="Cơ sở dữ liệu (INT2211-02) học tại B1-204 Thứ 2 Ca 1; buổi thực hành Thứ 5 đang chờ xếp phòng.",
                is_unread=True,
            ),
            Notification(
                target_username="sv_minhanh",
                category="Kết quả duyệt",
                tone="g",
                message="Yêu cầu mượn phòng TV-301 phục vụ ôn tập nhóm đã được Phòng Đào tạo phê duyệt.",
                is_unread=True,
            ),
        ]
    )

    write_audit_log(
        db,
        None,
        action="SEED_DEMO_DATA",
        target="CAMS Database",
        new_value=f"{len(demo_rooms)} phòng, {len(demo_classes)} lớp, {len(demo_sessions)} buổi học",
        reason="Khởi tạo dữ liệu mẫu phục vụ kiểm thử & demo",
    )
    db.commit()

    return {
        "seeded": True,
        "rooms": len(demo_rooms),
        "classes": len(demo_classes),
        "sessions": len(demo_sessions),
    }


@ops_router.post("/demo/seed", summary="Nạp / Khởi tạo lại bộ dữ liệu mẫu Demo")
def trigger_demo_seed(
    reset: bool = Query(default=False, description="true = làm mới lại dữ liệu mẫu ban đầu"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if reset and (not current_user or current_user.role not in (ROLE_ADMIN, ROLE_OFFICER)):
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin hoặc Cán bộ Đào tạo mới được làm mới toàn bộ dữ liệu mẫu",
        )
    info = seed_demo_dataset(db, reset=reset)
    return {"message": "Đã đồng bộ dữ liệu mẫu thành công", **info}

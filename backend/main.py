from __future__ import annotations

import csv
import os
from datetime import time
from io import BytesIO, StringIO
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from allocation import (
    Booking,
    Room as RoomDTO,
    SessionRequest,
    ViolationCode,
    parse_equipment,
    validate_assignment,
)
from allocation_router import allocation_router
from auth import (
    ROLE_ADMIN,
    ROLE_OFFICER,
    User,
    auth_router,
    require_role,
    write_audit_log,
)
from database import Base, SessionLocal, engine, get_db
from excel_service import read_timetable_excel
from models import CourseClass, Notification, Room, TimetableSession
from ops_router import (
    WEEKDAY_LABELS,
    check_final_closure,
    check_first_closure,
    ops_router,
    seed_demo_dataset,
)
from schemas import (
    CourseClassCreate,
    CourseClassResponse,
    RoomCreate,
    RoomResponse,
    TimetableSessionCreate,
    TimetableSessionResponse,
)


def _ensure_sqlite_migrations() -> None:
    """Đảm bảo CSDL SQLite cũ tự bổ sung cột mới mà không làm mất dữ liệu."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "course_classes" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("course_classes")}
        if "lecturer" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE course_classes ADD COLUMN lecturer VARCHAR(100)"))
    if "users" in inspector.get_table_names():
        u_cols = {c["name"] for c in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "student_code" not in u_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN student_code VARCHAR(30)"))
            if "department" not in u_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100)"))


_ensure_sqlite_migrations()

if os.getenv("AUTO_SEED", "true").lower() != "false":
    with SessionLocal() as _startup_db:
        seed_demo_dataset(_startup_db, reset=False)


app = FastAPI(
    title="CAMS - Classroom Allocation Management System",
    description="Hệ thống Quản lý Phòng học, Xếp thời khóa biểu Tự động & Phân quyền RBAC (Nhóm 6)",
    version="1.0.0",
)

# Cấu hình CORS hỗ trợ cả Local (Vite 5173 / Figma Make 8443) và Production (Vercel / Render)
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8443,http://localhost:3000,https://cams-nhom6.vercel.app",
)
cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|figma\.site|onrender\.com)|http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(allocation_router)
app.include_router(ops_router)


@app.get("/")
def read_root():
    return {
        "message": "CAMS Backend is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ==========================================
# HÀM KIỂM TRA RÀNGNG BUỘC DÙNG CHUNG
# ==========================================

def _validate_session_placement(
    db: Session,
    course_class: CourseClass,
    weekday: int,
    start_time: time,
    end_time: time,
    room_id: Optional[int],
    ignore_session_id: Optional[int] = None,
    allow_overload: bool = False,
) -> Optional[Room]:
    # 1. Kiểm tra chính lớp học phần đó không bị trùng giờ với buổi khác của cùng lớp
    class_conflict_q = db.query(TimetableSession).filter(
        TimetableSession.class_id == course_class.id,
        TimetableSession.weekday == weekday,
        TimetableSession.start_time < end_time,
        TimetableSession.end_time > start_time,
    )
    if ignore_session_id is not None:
        class_conflict_q = class_conflict_q.filter(TimetableSession.id != ignore_session_id)
    if class_conflict_q.first() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Lớp {course_class.class_code} đã có lịch học trùng vào khung giờ này",
        )

    if room_id is None:
        return None

    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")

    booked_rows = (
        db.query(TimetableSession, CourseClass)
        .join(CourseClass, CourseClass.id == TimetableSession.class_id)
        .filter(TimetableSession.room_id.isnot(None))
        .all()
    )
    bookings = [
        Booking(s.id, s.room_id, s.weekday, s.start_time, s.end_time, c.lecturer)
        for s, c in booked_rows
    ]
    req = SessionRequest(
        session_id=ignore_session_id or 0,
        class_code=course_class.class_code,
        course_name=course_class.course_name,
        student_count=course_class.student_count,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
        required_room_type=course_class.required_room_type,
        required_equipment=parse_equipment(course_class.required_equipment),
        lecturer=course_class.lecturer,
    )
    room_dto = RoomDTO(
        room.id,
        room.room_code,
        room.capacity,
        room.room_type,
        parse_equipment(room.equipment),
    )

    violations = validate_assignment(req, room_dto, bookings, ignore_session_id=ignore_session_id)
    if violations:
        # BR-01 (Trùng phòng / Trùng giảng viên / Dữ liệu sai): Luôn chặn cứng 409
        hard_codes = {
            ViolationCode.ROOM_TIME_CONFLICT,
            ViolationCode.LECTURER_TIME_CONFLICT,
            ViolationCode.INVALID_DATA,
        }
        hard_v = [v for v in violations if v.code in hard_codes]
        if hard_v:
            # Nếu trùng phòng, nêu rõ mã lớp đang chiếm phòng theo đúng chuẩn OFF-05 / BR-01
            if hard_v[0].code == ViolationCode.ROOM_TIME_CONFLICT:
                occupying = next(
                    (
                        c.class_code
                        for s, c in booked_rows
                        if s.id != ignore_session_id
                        and s.room_id == room.id
                        and s.weekday == weekday
                        and s.start_time < end_time
                        and s.end_time > start_time
                    ),
                    None,
                )
                if occupying:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Xung đột: Phòng {room.room_code} đã được gán cho lớp {occupying} "
                            f"vào {WEEKDAY_LABELS.get(weekday, f'Thứ {weekday + 1}')} "
                            f"({start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')})"
                        ),
                    )
            raise HTTPException(status_code=409, detail=hard_v[0].message)

        # BR-02: Nếu cán bộ chưa xác nhận ghi đè cảnh báo quá tải (allow_overload=False) -> báo 409 kèm chi tiết
        if not allow_overload:
            raise HTTPException(status_code=409, detail=violations[0].message)

    return room


# ==========================================
# API QUẢN LÝ PHÒNG HỌC (ADM-02)
# ==========================================

@app.get("/api/rooms", response_model=list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.room_code).all()


@app.get("/api/rooms/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")
    return room


@app.post(
    "/api/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    room = Room(**room_data.model_dump())
    db.add(room)

    try:
        write_audit_log(
            db,
            current_user,
            action="CREATE_ROOM",
            target=room.room_code,
            new_value=f"{room.building} · {room.capacity} chỗ · {room.room_type}",
        )
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã phòng bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return room


@app.put("/api/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")

    old_info = f"{room.room_code} ({room.capacity} chỗ)"
    for field, value in room_data.model_dump().items():
        setattr(room, field, value)

    try:
        write_audit_log(
            db,
            current_user,
            action="UPDATE_ROOM",
            target=room.room_code,
            old_value=old_info,
            new_value=f"{room.room_code} ({room.capacity} chỗ)",
        )
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã phòng bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return room


@app.delete("/api/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng học")

    existing_session = (
        db.query(TimetableSession)
        .filter(TimetableSession.room_id == room_id)
        .first()
    )
    if existing_session is not None:
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa phòng học đang có lịch trong thời khóa biểu",
        )

    code = room.room_code
    db.delete(room)
    write_audit_log(db, current_user, action="DELETE_ROOM", target=code)
    db.commit()

    return {"message": "Đã xóa phòng học thành công"}


# ==========================================
# API QUẢN LÝ LỚP HỌC PHẦN
# ==========================================

@app.get("/api/classes", response_model=list[CourseClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(CourseClass).order_by(CourseClass.class_code).all()


@app.get("/api/classes/{class_id}", response_model=CourseClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    course_class = db.query(CourseClass).filter(CourseClass.id == class_id).first()
    if course_class is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học phần")
    return course_class


@app.post(
    "/api/classes",
    response_model=CourseClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    class_data: CourseClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    course_class = CourseClass(**class_data.model_dump())
    db.add(course_class)

    try:
        write_audit_log(
            db,
            current_user,
            action="CREATE_CLASS",
            target=course_class.class_code,
            new_value=f"{course_class.course_name} ({course_class.student_count} SV)",
        )
        db.commit()
        db.refresh(course_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã lớp học phần đã tồn tại hoặc dữ liệu vi phạm ràng buộc",
        )

    return course_class


@app.put("/api/classes/{class_id}", response_model=CourseClassResponse)
def update_class(
    class_id: int,
    class_data: CourseClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    course_class = db.query(CourseClass).filter(CourseClass.id == class_id).first()
    if course_class is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học phần")

    for field, value in class_data.model_dump().items():
        setattr(course_class, field, value)

    try:
        write_audit_log(
            db,
            current_user,
            action="UPDATE_CLASS",
            target=course_class.class_code,
            new_value=f"{course_class.course_name} ({course_class.student_count} SV)",
        )
        db.commit()
        db.refresh(course_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã lớp học phần bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return course_class


@app.delete("/api/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    course_class = db.query(CourseClass).filter(CourseClass.id == class_id).first()
    if course_class is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học phần")

    existing_session = (
        db.query(TimetableSession)
        .filter(TimetableSession.class_id == class_id)
        .first()
    )
    if existing_session is not None:
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa lớp học phần đang có thời khóa biểu",
        )

    code = course_class.class_code
    db.delete(course_class)
    write_audit_log(db, current_user, action="DELETE_CLASS", target=code)
    db.commit()

    return {"message": "Đã xóa lớp học phần thành công"}


# ==========================================
# API QUẢN LÝ THỜI KHÓA BIỂU & ĐIỀU CHỈNH PHÒNG (OFF-04, OFF-05, OFF-06)
# ==========================================

@app.get(
    "/api/timetable/sessions",
    response_model=list[TimetableSessionResponse],
)
def get_timetable_sessions(db: Session = Depends(get_db)):
    return (
        db.query(TimetableSession)
        .order_by(TimetableSession.weekday, TimetableSession.start_time)
        .all()
    )


@app.get(
    "/api/timetable/sessions/{session_id}",
    response_model=TimetableSessionResponse,
)
def get_timetable_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TimetableSession).filter(TimetableSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học")
    return session


@app.post(
    "/api/timetable/sessions",
    response_model=TimetableSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_timetable_session(
    session_data: TimetableSessionCreate,
    allow_overload: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    check_final_closure(db)

    course_class = db.query(CourseClass).filter(CourseClass.id == session_data.class_id).first()
    if course_class is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học phần")

    room = _validate_session_placement(
        db=db,
        course_class=course_class,
        weekday=session_data.weekday,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        room_id=session_data.room_id,
        allow_overload=allow_overload,
    )

    session = TimetableSession(**session_data.model_dump())
    db.add(session)

    try:
        write_audit_log(
            db,
            current_user,
            action="CREATE_SESSION",
            target=f"{course_class.class_code} ({WEEKDAY_LABELS.get(session_data.weekday, '')})",
            new_value=room.room_code if room else "Chờ xếp phòng",
        )
        db.commit()
        db.refresh(session)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dữ liệu buổi học vi phạm ràng buộc database")

    return session


@app.put(
    "/api/timetable/sessions/{session_id}",
    response_model=TimetableSessionResponse,
)
def update_timetable_session(
    session_id: int,
    session_data: TimetableSessionCreate,
    allow_overload: bool = Query(default=False, description="Cho phép lưu kèm cảnh báo quá tải sức chứa (BR-02)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    check_final_closure(db)

    session = db.query(TimetableSession).filter(TimetableSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học")

    course_class = db.query(CourseClass).filter(CourseClass.id == session_data.class_id).first()
    if course_class is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học phần")

    old_room = db.query(Room).filter(Room.id == session.room_id).first() if session.room_id else None

    new_room = _validate_session_placement(
        db=db,
        course_class=course_class,
        weekday=session_data.weekday,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        room_id=session_data.room_id,
        ignore_session_id=session_id,
        allow_overload=allow_overload,
    )

    old_code = old_room.room_code if old_room else "Chờ xếp phòng"
    new_code = new_room.room_code if new_room else "Chờ xếp phòng"

    for field, value in session_data.model_dump().items():
        setattr(session, field, value)

    try:
        if old_code != new_code:
            write_audit_log(
                db,
                current_user,
                action="MANUAL_ASSIGN_ROOM",
                target=f"{course_class.class_code} (Session #{session.id})",
                old_value=old_code,
                new_value=new_code,
                reason="Điều chỉnh phân phòng thủ công",
            )
            if new_room:
                db.add(
                    Notification(
                        target_role=None,
                        category="Đổi phòng",
                        tone="b",
                        message=(
                            f"Lớp {course_class.course_name} ({course_class.class_code}) được cập nhật phòng: "
                            f"{old_code} -> {new_code} ({WEEKDAY_LABELS.get(session.weekday, '')})."
                        ),
                    )
                )
        db.commit()
        db.refresh(session)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dữ liệu buổi học vi phạm ràng buộc database")

    return session


@app.delete("/api/timetable/sessions/{session_id}")
def delete_timetable_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    check_final_closure(db)

    session = db.query(TimetableSession).filter(TimetableSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy buổi học")

    db.delete(session)
    write_audit_log(db, current_user, action="DELETE_SESSION", target=f"Session #{session_id}")
    db.commit()
    return {"message": "Đã xóa buổi học thành công"}


# ==========================================
# TẢI FILE MẪU & IMPORT EXCEL / CSV (OFF-01)
# ==========================================

@app.get("/api/timetable/template", response_class=StreamingResponse, summary="Tải file Excel mẫu TKB chuẩn")
def download_timetable_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "TimetableTemplate"
    ws.append([
        "class_code",
        "course_name",
        "lecturer",
        "student_count",
        "weekday",
        "start_time",
        "end_time",
        "room_code",
        "required_room_type",
        "required_equipment",
    ])
    ws.append([
        "INT3202-01",
        "Hệ quản trị CSDL",
        "TS. Nguyễn Văn An",
        52,
        2,
        "07:00:00",
        "09:30:00",
        "",
        "classroom",
        "Máy chiếu, Điều hòa",
    ])
    ws.append([
        "INT3202-LAB",
        "Thực hành Hệ QTCSDL",
        "ThS. Lê Hoàng Nam",
        40,
        5,
        "13:00:00",
        "15:30:00",
        "",
        "lab",
        "Máy tính, Máy chiếu",
    ])
    ws.freeze_panes = "A2"
    for col_letter, width in [("A", 16), ("B", 24), ("C", 22), ("D", 14), ("E", 10), ("F", 13), ("G", 13), ("H", 14), ("I", 18), ("J", 24)]:
        ws.column_dimensions[col_letter].width = width

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CAMS_timetable_template.xlsx"'},
    )


@app.post(
    "/api/timetable/import",
    status_code=status.HTTP_201_CREATED,
)
async def import_timetable_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    check_first_closure(db)

    if not file.filename or not file.filename.lower().endswith((".xlsx", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file thời khóa biểu định dạng .xlsx hoặc .csv",
        )

    contents = await file.read(5 * 1024 * 1024 + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="File tải lên đang trống")
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File vượt quá giới hạn 5 MB")

    result = read_timetable_excel(contents, filename=file.filename)

    if result["errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "File thời khóa biểu có dữ liệu không hợp lệ",
                "errors": result["errors"],
            },
        )

    if not result["rows"]:
        raise HTTPException(status_code=422, detail="File không có dữ liệu thời khóa biểu")

    sessions_to_create: list[TimetableSession] = []
    created_classes_cache: dict[str, CourseClass] = {}
    errors: list[dict] = []

    for row_number, row in enumerate(result["rows"], start=2):
        course_class: Optional[CourseClass] = None
        c_code = row.get("class_code")
        c_name = row.get("course_name")

        if c_code:
            course_class = created_classes_cache.get(c_code) or (
                db.query(CourseClass).filter(CourseClass.class_code == c_code).first()
            )
            if course_class is None:
                # Tự động tạo lớp học phần nếu file Excel thô cung cấp đủ thông tin (OFF-01)
                course_class = CourseClass(
                    class_code=c_code,
                    course_name=c_name or c_code,
                    lecturer=row.get("lecturer"),
                    student_count=row.get("student_count") or 40,
                    required_room_type=row.get("required_room_type") or "classroom",
                    required_equipment=row.get("required_equipment"),
                )
                db.add(course_class)
                db.flush()
                created_classes_cache[c_code] = course_class
            else:
                if row.get("lecturer") and not course_class.lecturer:
                    course_class.lecturer = row["lecturer"]
        elif c_name:
            matched_classes = db.query(CourseClass).filter(CourseClass.course_name == c_name).all()
            if len(matched_classes) == 0:
                errors.append({"row": row_number, "message": f"Không tìm thấy môn học {c_name}"})
                continue
            if len(matched_classes) > 1:
                errors.append(
                    {
                        "row": row_number,
                        "message": f"Tên môn học {c_name} khớp với nhiều lớp học phần. Cần bổ sung cột class_code.",
                    }
                )
                continue
            course_class = matched_classes[0]

        assert course_class is not None

        start_time = time.fromisoformat(row["start_time"])
        end_time = time.fromisoformat(row["end_time"])

        class_conflict = (
            db.query(TimetableSession)
            .filter(
                TimetableSession.class_id == course_class.id,
                TimetableSession.weekday == row["weekday"],
                TimetableSession.start_time < end_time,
                TimetableSession.end_time > start_time,
            )
            .first()
        )
        if class_conflict is not None:
            errors.append(
                {
                    "row": row_number,
                    "message": f"Lớp {course_class.class_code} đã có lịch trong khoảng thời gian này",
                }
            )
            continue

        batch_class_conflict = any(
            previous.class_id == course_class.id
            and previous.weekday == row["weekday"]
            and previous.start_time < end_time
            and previous.end_time > start_time
            for previous in sessions_to_create
        )
        if batch_class_conflict:
            errors.append(
                {
                    "row": row_number,
                    "message": f"Lớp {course_class.class_code} bị trùng lịch với dòng khác trong file",
                }
            )
            continue

        room: Optional[Room] = None
        room_code = row["room_code"]
        if room_code:
            room = db.query(Room).filter(Room.room_code == room_code).first()
            if room is None:
                errors.append({"row": row_number, "message": f"Không tìm thấy phòng {room_code}"})
                continue
            if room.capacity < course_class.student_count:
                errors.append({"row": row_number, "message": f"Phòng {room_code} không đủ sức chứa"})
                continue
            if room.room_type != course_class.required_room_type:
                errors.append({"row": row_number, "message": f"Phòng {room_code} không đúng loại phòng"})
                continue

            missing_eq = parse_equipment(course_class.required_equipment) - parse_equipment(room.equipment)
            if missing_eq:
                errors.append(
                    {
                        "row": row_number,
                        "message": f"Phòng {room_code} thiếu thiết bị: " + ", ".join(sorted(missing_eq)),
                    }
                )
                continue

            room_conflict = (
                db.query(TimetableSession)
                .filter(
                    TimetableSession.room_id == room.id,
                    TimetableSession.weekday == row["weekday"],
                    TimetableSession.start_time < end_time,
                    TimetableSession.end_time > start_time,
                )
                .first()
            )
            if room_conflict is not None:
                errors.append({"row": row_number, "message": f"Phòng {room_code} đã có lịch trong khoảng thời gian này"})
                continue

            batch_room_conflict = any(
                previous.room_id == room.id
                and previous.weekday == row["weekday"]
                and previous.start_time < end_time
                and previous.end_time > start_time
                for previous in sessions_to_create
            )
            if batch_room_conflict:
                errors.append(
                    {
                        "row": row_number,
                        "message": f"Phòng {room_code} bị trùng lịch với một dòng khác trong file",
                    }
                )
                continue

        sessions_to_create.append(
            TimetableSession(
                class_id=course_class.id,
                weekday=row["weekday"],
                start_time=start_time,
                end_time=end_time,
                room_id=room.id if room is not None else None,
            )
        )

    if errors:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Có dữ liệu không hợp lệ. Không có buổi học nào được nhập.",
                "errors": errors,
            },
        )

    db.add_all(sessions_to_create)

    try:
        write_audit_log(
            db,
            current_user,
            action="IMPORT_TIMETABLE",
            target=file.filename,
            new_value=f"Đã nhập {len(sessions_to_create)} buổi học",
        )
        db.commit()
        for session in sessions_to_create:
            db.refresh(session)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dữ liệu file vi phạm ràng buộc database")

    return {
        "message": "Nhập thời khóa biểu thành công",
        "imported_count": len(sessions_to_create),
        "sessions": [
            {
                "id": s.id,
                "class_id": s.class_id,
                "weekday": s.weekday,
                "start_time": s.start_time.strftime("%H:%M:%S"),
                "end_time": s.end_time.strftime("%H:%M:%S"),
                "room_id": s.room_id,
            }
            for s in sessions_to_create
        ],
    }


# ==========================================
# EXPORT THỜI KHÓA BIỂU RA EXCEL / CSV (OFF-08)
# ==========================================

@app.get(
    "/api/timetable/export",
    response_class=StreamingResponse,
)
def export_timetable_excel(
    fmt: str = Query(default="xlsx", pattern="^(xlsx|csv)$"),
    building: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN, ROLE_OFFICER])),
):
    q = (
        db.query(TimetableSession, CourseClass, Room)
        .join(CourseClass, TimetableSession.class_id == CourseClass.id)
        .outerjoin(Room, TimetableSession.room_id == Room.id)
    )
    if building and building != "Tất cả":
        q = q.filter(Room.building.ilike(f"%{building.strip()}%"))

    sessions = q.order_by(TimetableSession.weekday, TimetableSession.start_time).all()

    headers_row = [
        "class_code",
        "course_name",
        "lecturer",
        "student_count",
        "weekday",
        "start_time",
        "end_time",
        "room_code",
        "building",
    ]

    if fmt == "csv":
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(headers_row)
        for s, c, r in sessions:
            writer.writerow([
                c.class_code,
                c.course_name,
                c.lecturer or "",
                c.student_count,
                s.weekday,
                s.start_time.strftime("%H:%M:%S"),
                s.end_time.strftime("%H:%M:%S"),
                r.room_code if r else "",
                r.building if r else "",
            ])
        csv_bytes = sio.getvalue().encode("utf-8-sig")
        return StreamingResponse(
            BytesIO(csv_bytes),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="CAMS_timetable_export.csv"'},
        )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Timetable"
    worksheet.append(headers_row)

    for s, c, r in sessions:
        worksheet.append([
            c.class_code,
            c.course_name,
            c.lecturer or "",
            c.student_count,
            s.weekday,
            s.start_time.strftime("%H:%M:%S"),
            s.end_time.strftime("%H:%M:%S"),
            r.room_code if r else "",
            r.building if r else "",
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    for col_letter, width in [("A", 16), ("B", 28), ("C", 22), ("D", 14), ("E", 10), ("F", 13), ("G", 13), ("H", 14), ("I", 16)]:
        worksheet.column_dimensions[col_letter].width = width

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="CAMS_timetable_export.xlsx"'},
    )


from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)

from datetime import time
from excel_service import read_timetable_excel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db
from models import Room, CourseClass, TimetableSession
from schemas import (
    RoomCreate,
    RoomResponse,
    CourseClassCreate,
    CourseClassResponse,
    TimetableSessionCreate,
    TimetableSessionResponse,
)
from io import BytesIO
from openpyxl import Workbook
from fastapi.responses import StreamingResponse


# Tạo bảng trong database nếu bảng chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CAMS - Classroom Allocation Management System",
    description="API quản lý phòng học và thời khóa biểu",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "CAMS Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# 1. Lấy danh sách phòng học
@app.get("/api/rooms", response_model=list[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).order_by(Room.room_code).all()


# 2. Lấy thông tin một phòng theo ID
@app.get("/api/rooms/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy phòng học",
        )

    return room


# 3. Thêm phòng học
@app.post(
    "/api/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    room = Room(**room_data.model_dump())
    db.add(room)

    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã phòng bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return room


# 4. Cập nhật phòng học
@app.put("/api/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomCreate,
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy phòng học",
        )

    for field, value in room_data.model_dump().items():
        setattr(room, field, value)

    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã phòng bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return room


# 5. Xóa phòng học
@app.delete("/api/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy phòng học",
        )

    db.delete(room)
    db.commit()

    return {"message": "Đã xóa phòng học thành công"}

# ==========================================
# API QUẢN LÝ LỚP HỌC PHẦN
# ==========================================

# 1. Lấy danh sách lớp học phần
@app.get("/api/classes", response_model=list[CourseClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(CourseClass).order_by(
        CourseClass.class_code
    ).all()


# 2. Xem chi tiết một lớp học phần
@app.get("/api/classes/{class_id}", response_model=CourseClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    course_class = db.query(CourseClass).filter(
        CourseClass.id == class_id
    ).first()

    if course_class is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lớp học phần",
        )

    return course_class


# 3. Thêm lớp học phần
@app.post(
    "/api/classes",
    response_model=CourseClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    class_data: CourseClassCreate,
    db: Session = Depends(get_db),
):
    course_class = CourseClass(**class_data.model_dump())

    db.add(course_class)

    try:
        db.commit()
        db.refresh(course_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã lớp học phần đã tồn tại hoặc dữ liệu vi phạm ràng buộc",
        )

    return course_class


# 4. Cập nhật lớp học phần
@app.put(
    "/api/classes/{class_id}",
    response_model=CourseClassResponse,
)
def update_class(
    class_id: int,
    class_data: CourseClassCreate,
    db: Session = Depends(get_db),
):
    course_class = db.query(CourseClass).filter(
        CourseClass.id == class_id
    ).first()

    if course_class is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lớp học phần",
        )

    for field, value in class_data.model_dump().items():
        setattr(course_class, field, value)

    try:
        db.commit()
        db.refresh(course_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Mã lớp học phần bị trùng hoặc dữ liệu vi phạm ràng buộc",
        )

    return course_class


# 5. Xóa lớp học phần
@app.delete("/api/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
):
    course_class = db.query(CourseClass).filter(
        CourseClass.id == class_id
    ).first()

    if course_class is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lớp học phần",
        )

    # Không xóa lớp nếu đã có buổi học trong thời khóa biểu
    existing_session = db.query(TimetableSession).filter(
        TimetableSession.class_id == class_id
    ).first()

    if existing_session is not None:
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa lớp học phần đang có thời khóa biểu",
        )

    db.delete(course_class)
    db.commit()

    return {"message": "Đã xóa lớp học phần thành công"}

# ==========================================
# API QUẢN LÝ THỜI KHÓA BIỂU
# ==========================================

# 1. Lấy danh sách các buổi học
@app.get(
    "/api/timetable/sessions",
    response_model=list[TimetableSessionResponse],
)
def get_timetable_sessions(db: Session = Depends(get_db)):
    return db.query(TimetableSession).order_by(
        TimetableSession.weekday,
        TimetableSession.start_time,
    ).all()

# Xem chi tiết một buổi học theo ID
@app.get(
    "/api/timetable/sessions/{session_id}",
    response_model=TimetableSessionResponse,
)
def get_timetable_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = db.query(TimetableSession).filter(
        TimetableSession.id == session_id
    ).first()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy buổi học",
        )

    return session



# 2. Tạo buổi học mới
@app.post(
    "/api/timetable/sessions",
    response_model=TimetableSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_timetable_session(
    session_data: TimetableSessionCreate,
    db: Session = Depends(get_db),
):
    # Kiểm tra lớp học phần có tồn tại không
    course_class = db.query(CourseClass).filter(
        CourseClass.id == session_data.class_id
    ).first()

    if course_class is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lớp học phần",
        )

    # Nếu buổi học đã được gán phòng
    if session_data.room_id is not None:

        room = db.query(Room).filter(
            Room.id == session_data.room_id
        ).first()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng học",
            )

        # Kiểm tra sức chứa
        if room.capacity < course_class.student_count:
            raise HTTPException(
                status_code=409,
                detail="Sức chứa phòng không đủ cho lớp học",
            )

        # Kiểm tra loại phòng
        if room.room_type != course_class.required_room_type:
            raise HTTPException(
                status_code=409,
                detail="Loại phòng không phù hợp với lớp học",
            )
        
        # Kiểm tra thiết bị phòng học
        required_equipment = {
            item.strip().casefold()
            for item in (course_class.required_equipment or "").split(",")
            if item.strip()
        }

        available_equipment = {
            item.strip().casefold()
            for item in (room.equipment or "").split(",")
            if item.strip()
        }

        missing_equipment = required_equipment - available_equipment

        if missing_equipment:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Phòng học thiếu thiết bị yêu cầu: "
                    + ", ".join(sorted(missing_equipment))
                ),
            )


        # Kiểm tra trùng lịch phòng
        conflict = db.query(TimetableSession).filter(
            TimetableSession.room_id == session_data.room_id,
            TimetableSession.weekday == session_data.weekday,
            TimetableSession.start_time < session_data.end_time,
            TimetableSession.end_time > session_data.start_time,
        ).first()

        if conflict is not None:
            raise HTTPException(
                status_code=409,
                detail="Phòng học đã có lịch vào khoảng thời gian này",
            )

    # Tạo buổi học và lưu vào database
    session = TimetableSession(**session_data.model_dump())

    db.add(session)

    try:
        db.commit()
        db.refresh(session)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Dữ liệu buổi học vi phạm ràng buộc database",
        )

    return session

# ==========================================
# CẬP NHẬT BUỔI HỌC
# ==========================================

@app.put(
    "/api/timetable/sessions/{session_id}",
    response_model=TimetableSessionResponse,
)
def update_timetable_session(
    session_id: int,
    session_data: TimetableSessionCreate,
    db: Session = Depends(get_db),
):
    # 1. Kiểm tra buổi học có tồn tại không
    session = db.query(TimetableSession).filter(
        TimetableSession.id == session_id
    ).first()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy buổi học",
        )

    # 2. Kiểm tra lớp học phần có tồn tại không
    course_class = db.query(CourseClass).filter(
        CourseClass.id == session_data.class_id
    ).first()

    if course_class is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lớp học phần",
        )

    # 3. Nếu có chỉ định phòng học thì kiểm tra phòng
    if session_data.room_id is not None:

        room = db.query(Room).filter(
            Room.id == session_data.room_id
        ).first()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng học",
            )

        # 4. Kiểm tra sức chứa
        if room.capacity < course_class.student_count:
            raise HTTPException(
                status_code=409,
                detail="Sức chứa phòng không đủ cho lớp học",
            )

        # 5. Kiểm tra loại phòng
        if room.room_type != course_class.required_room_type:
            raise HTTPException(
                status_code=409,
                detail="Loại phòng không phù hợp với lớp học",
            )

        # 6. Kiểm tra thiết bị
        required_equipment = {
            item.strip().casefold()
            for item in (
                course_class.required_equipment or ""
            ).split(",")
            if item.strip()
        }

        available_equipment = {
            item.strip().casefold()
            for item in (room.equipment or "").split(",")
            if item.strip()
        }

        missing_equipment = (
            required_equipment - available_equipment
        )

        if missing_equipment:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Phòng học thiếu thiết bị yêu cầu: "
                    + ", ".join(sorted(missing_equipment))
                ),
            )

        # 7. Kiểm tra trùng lịch phòng
        # Loại trừ chính buổi học đang được cập nhật
        conflict = db.query(TimetableSession).filter(
            TimetableSession.id != session_id,
            TimetableSession.room_id == session_data.room_id,
            TimetableSession.weekday == session_data.weekday,
            TimetableSession.start_time < session_data.end_time,
            TimetableSession.end_time > session_data.start_time,
        ).first()

        if conflict is not None:
            raise HTTPException(
                status_code=409,
                detail="Phòng học đã có lịch vào khoảng thời gian này",
            )

    # 8. Cập nhật thông tin buổi học
    for field, value in session_data.model_dump().items():
        setattr(session, field, value)

    try:
        db.commit()
        db.refresh(session)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Dữ liệu buổi học vi phạm ràng buộc database",
        )

    return session

# ==========================================
# XÓA BUỔI HỌC
# ==========================================

@app.delete("/api/timetable/sessions/{session_id}")
def delete_timetable_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    # Kiểm tra buổi học có tồn tại không
    session = db.query(TimetableSession).filter(
        TimetableSession.id == session_id
    ).first()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy buổi học",
        )

    # Xóa buổi học khỏi database
    db.delete(session)
    db.commit()

    return {
        "message": "Đã xóa buổi học thành công"
    }

# ==========================================
# IMPORT THỜI KHÓA BIỂU TỪ FILE EXCEL
# ==========================================

@app.post(
    "/api/timetable/import",
    status_code=status.HTTP_201_CREATED,
)

async def import_timetable_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Kiểm tra định dạng file
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file Excel có định dạng .xlsx",
        )

    # 2. Đọc nội dung file (giới hạn 5 MB)
    contents = await file.read(5 * 1024 * 1024 + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="File Excel đang trống",
        )

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File Excel vượt quá giới hạn 5 MB",
        )

    # 3. Đọc và kiểm tra dữ liệu Excel
    result = read_timetable_excel(contents)

    if result["errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "File Excel có dữ liệu không hợp lệ",
                "errors": result["errors"],
            },
        )

    if not result["rows"]:
        raise HTTPException(
            status_code=422,
            detail="File Excel không có dữ liệu thời khóa biểu",
        )

    # 4. Chuẩn bị dữ liệu
    sessions_to_create = []
    errors = []

    # Duyệt từng dòng trong file Excel
    for row_number, row in enumerate(result["rows"], start=2):

        # 4.1. Kiểm tra và tìm lớp học phần theo tên môn học
        matched_classes = db.query(CourseClass).filter(
            CourseClass.course_name == row["course_name"].strip()
        ).all()

        if len(matched_classes) == 0:
            errors.append({
                "row": row_number,
                "message": f"Không tìm thấy môn học {row['course_name']}",
            })
            continue

        if len(matched_classes) > 1:
            errors.append({
                "row": row_number,
                "message": (
                    f"Tên môn học {row['course_name']} "
                    "khớp với nhiều lớp học phần. "
                    "Cần bổ sung mã lớp hoặc nhóm lớp để phân biệt."
                ),
            })
            continue

        course_class = matched_classes[0]

        # 4.2. Chuyển đổi thời gian
        start_time = time.fromisoformat(row["start_time"])
        end_time = time.fromisoformat(row["end_time"])

        # 4.3. Kiểm tra trùng lịch của lớp trong database
        class_conflict = db.query(TimetableSession).filter(
            TimetableSession.class_id == course_class.id,
            TimetableSession.weekday == row["weekday"],
            TimetableSession.start_time < end_time,
            TimetableSession.end_time > start_time,
        ).first()

        if class_conflict is not None:
            errors.append({
                "row": row_number,
                "message": (
                    f"Môn học {row['course_name']} "
                    "đã có lịch trong khoảng thời gian này"
                ),
            })
            continue

        # 4.4. Kiểm tra trùng lịch lớp giữa các dòng Excel
        batch_class_conflict = any(
            previous.class_id == course_class.id
            and previous.weekday == row["weekday"]
            and previous.start_time < end_time
            and previous.end_time > start_time
            for previous in sessions_to_create
        )

        if batch_class_conflict:
            errors.append({
                "row": row_number,
                "message": (
                    f"Môn học {row['course_name']} "
                    "bị trùng lịch với dòng khác trong file Excel"
                ),
            })
            continue

        # 4.5. Kiểm tra phòng học nếu Excel có chỉ định phòng
        room = None
        room_code = row["room_code"]

        if room_code:
            room = db.query(Room).filter(
                Room.room_code == room_code
            ).first()

            if room is None:
                errors.append({
                    "row": row_number,
                    "message": f"Không tìm thấy phòng {room_code}",
                })
                continue

            # Kiểm tra sức chứa
            if room.capacity < course_class.student_count:
                errors.append({
                    "row": row_number,
                    "message": f"Phòng {room_code} không đủ sức chứa",
                })
                continue

            # Kiểm tra loại phòng
            if room.room_type != course_class.required_room_type:
                errors.append({
                    "row": row_number,
                    "message": f"Phòng {room_code} không đúng loại phòng",
                })
                continue

            # Kiểm tra thiết bị
            required_equipment = {
                item.strip().casefold()
                for item in (
                    course_class.required_equipment or ""
                ).split(",")
                if item.strip()
            }

            available_equipment = {
                item.strip().casefold()
                for item in (room.equipment or "").split(",")
                if item.strip()
            }

            missing_equipment = (
                required_equipment - available_equipment
            )

            if missing_equipment:
                errors.append({
                    "row": row_number,
                    "message": (
                        f"Phòng {room_code} thiếu thiết bị: "
                        + ", ".join(sorted(missing_equipment))
                    ),
                })
                continue

            # Kiểm tra trùng lịch phòng trong database
            room_conflict = db.query(TimetableSession).filter(
                TimetableSession.room_id == room.id,
                TimetableSession.weekday == row["weekday"],
                TimetableSession.start_time < end_time,
                TimetableSession.end_time > start_time,
            ).first()

            if room_conflict is not None:
                errors.append({
                    "row": row_number,
                    "message": (
                        f"Phòng {room_code} đã có lịch "
                        "trong khoảng thời gian này"
                    ),
                })
                continue

            # Kiểm tra trùng lịch phòng giữa các dòng Excel
            batch_room_conflict = any(
                previous.room_id == room.id
                and previous.weekday == row["weekday"]
                and previous.start_time < end_time
                and previous.end_time > start_time
                for previous in sessions_to_create
            )

            if batch_room_conflict:
                errors.append({
                    "row": row_number,
                    "message": (
                        f"Phòng {room_code} bị trùng lịch "
                        "với một dòng khác trong file Excel"
                    ),
                })
                continue

        # 4.6. Chuẩn bị buổi học
        session = TimetableSession(
            class_id=course_class.id,
            weekday=row["weekday"],
            start_time=start_time,
            end_time=end_time,
            room_id=room.id if room is not None else None,
        )

        sessions_to_create.append(session)

    # 5. Nếu có lỗi thì từ chối toàn bộ file
    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "Có dữ liệu không hợp lệ. "
                    "Không có buổi học nào được nhập."
                ),
                "errors": errors,
            },
        )

    # 6. Lưu toàn bộ dữ liệu hợp lệ vào database
    db.add_all(sessions_to_create)

    try:
        db.commit()

        for session in sessions_to_create:
            db.refresh(session)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Dữ liệu Excel vi phạm ràng buộc database",
        )

    # 7. Trả kết quả
    return {
        "message": "Nhập thời khóa biểu từ Excel thành công",
        "imported_count": len(sessions_to_create),
        "sessions": [
            {
                "id": session.id,
                "class_id": session.class_id,
                "weekday": session.weekday,
                "start_time": session.start_time.strftime("%H:%M:%S"),
                "end_time": session.end_time.strftime("%H:%M:%S"),
                "room_id": session.room_id,
            }
            for session in sessions_to_create
        ],
    }


# ==========================================
# EXPORT THỜI KHÓA BIỂU RA FILE EXCEL
# ==========================================

@app.get(
    "/api/timetable/export",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
            "description": "File Excel thời khóa biểu",
        }
    },
)
def export_timetable_excel(
    db: Session = Depends(get_db),
):
    # 1. Lấy dữ liệu buổi học, lớp học phần và phòng học
    sessions = (
        db.query(TimetableSession, CourseClass, Room)
        .join(
            CourseClass,
            TimetableSession.class_id == CourseClass.id,
        )
        .outerjoin(
            Room,
            TimetableSession.room_id == Room.id,
        )
        .order_by(
            TimetableSession.weekday,
            TimetableSession.start_time,
        )
        .all()
    )

    # 2. Tạo workbook Excel
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Timetable"

    # 3. Tạo tiêu đề cột
    worksheet.append([
    "course_name",
    "weekday",
    "start_time",
    "end_time",
    "room_code",
])

    # 4. Ghi dữ liệu vào Excel
    for session, course_class, room in sessions:
        worksheet.append([
            course_class.class_code,
            session.weekday,
            session.start_time.strftime("%H:%M:%S"),
            session.end_time.strftime("%H:%M:%S"),
            room.room_code if room else "",
        ])

    # 5. Định dạng bảng
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    worksheet.column_dimensions["A"].width = 20
    worksheet.column_dimensions["B"].width = 12
    worksheet.column_dimensions["C"].width = 15
    worksheet.column_dimensions["D"].width = 15
    worksheet.column_dimensions["E"].width = 18

    # 6. Lưu workbook vào bộ nhớ
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    # 7. Trả file Excel cho người dùng tải xuống
    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachmendef export_timetable_excelt; filename="CAMS_timetable_export.xlsx"'
            )
        },
    )





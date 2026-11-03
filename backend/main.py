
from fastapi import FastAPI, Depends, HTTPException, status
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



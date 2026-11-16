from datetime import time

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# =========================
# SCHEMAS PHÒNG HỌC
# =========================

class RoomCreate(BaseModel):
    room_code: str = Field(min_length=1, max_length=20)
    building: str = Field(min_length=1, max_length=100)
    floor: int | None = None
    capacity: int = Field(gt=0)
    room_type: str = Field(
        default="classroom",
        min_length=1,
        max_length=50,
    )
    equipment: str | None = None
    notes: str | None = None


class RoomResponse(RoomCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =========================
# SCHEMAS LỚP HỌC PHẦN
# =========================

class CourseClassCreate(BaseModel):
    class_code: str = Field(min_length=1, max_length=30)
    course_name: str = Field(min_length=1, max_length=150)
    student_count: int = Field(gt=0)

    required_room_type: str = Field(
        default="classroom",
        min_length=1,
        max_length=50,
    )

    required_equipment: str | None = None


class CourseClassResponse(CourseClassCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =========================
# SCHEMAS BUỔI HỌC
# =========================

class TimetableSessionCreate(BaseModel):
    class_id: int = Field(gt=0)
    weekday: int = Field(ge=1, le=7)

    start_time: time
    end_time: time

    room_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError(
                "Giờ kết thúc phải sau giờ bắt đầu"
            )
        return self


class TimetableSessionResponse(TimetableSessionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
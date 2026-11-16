from datetime import time

import pytest

from allocation import (
    Booking,
    Room,
    SessionRequest,
    ViolationCode as V,
    allocate,
    parse_equipment,
    times_overlap,
    validate_assignment,
)

T = time


def room(id, cap, code=None, typ="classroom", eq=""):
    return Room(id, code or f"R{id}", cap, typ, parse_equipment(eq))


def req(sid, n=30, wd=2, s=T(7, 0), e=T(9, 30), typ="classroom", eq="", lec=None, code=None):
    return SessionRequest(
        session_id=sid,
        class_code=code or f"C{sid}",
        student_count=n,
        weekday=wd,
        start_time=s,
        end_time=e,
        required_room_type=typ,
        required_equipment=parse_equipment(eq),
        lecturer=lec,
    )


def codes(violations):
    return {v.code for v in violations}


# ---------- times_overlap ----------

@pytest.mark.parametrize(
    "a,b,expected",
    [
        ((T(7), T(9)), (T(8), T(10)), True),     # giao một phần
        ((T(7), T(9)), (T(9), T(11)), False),    # sát nhau không tính trùng
        ((T(7), T(11)), (T(8), T(9)), True),     # chứa nhau
        ((T(7), T(9)), (T(9, 1), T(11)), False),
        ((T(7), T(9)), (T(7), T(9)), True),      # y hệt
    ],
)
def test_times_overlap(a, b, expected):
    assert times_overlap(*a, *b) is expected


# ---------- validate_assignment: từng ràng buộc ----------

def test_valid_assignment_has_no_violations():
    assert validate_assignment(req(1, 30), room(1, 40), []) == []


def test_capacity_exact_is_ok_and_one_short_fails():
    assert validate_assignment(req(1, 40), room(1, 40), []) == []
    assert codes(validate_assignment(req(1, 41), room(1, 40), [])) == {V.ROOM_CAPACITY}


def test_room_type_mismatch():
    v = validate_assignment(req(1, typ="lab"), room(1, 50, typ="classroom"), [])
    assert codes(v) == {V.ROOM_TYPE}


def test_equipment_missing_is_case_and_space_insensitive():
    r = room(1, 50, eq="Máy chiếu , Điều hòa")
    assert validate_assignment(req(1, eq="máy chiếu"), r, []) == []
    v = validate_assignment(req(1, eq="máy chiếu, loa"), r, [])
    assert codes(v) == {V.ROOM_EQUIPMENT}
    assert "loa" in v[0].message


def test_room_time_conflict_same_day_overlap():
    b = Booking(99, 1, 2, T(8), T(10))
    v = validate_assignment(req(1, s=T(7), e=T(9)), room(1, 50), [b])
    assert codes(v) == {V.ROOM_TIME_CONFLICT}


def test_room_back_to_back_and_other_day_and_other_room_are_ok():
    r = room(1, 50)
    assert validate_assignment(req(1, s=T(9), e=T(11)), r, [Booking(99, 1, 2, T(7), T(9))]) == []
    assert validate_assignment(req(1), r, [Booking(99, 1, 3, T(7), T(9, 30))]) == []  # khác thứ
    assert validate_assignment(req(1), r, [Booking(99, 2, 2, T(7), T(9, 30))]) == []  # khác phòng


def test_lecturer_conflict_even_in_different_room():
    b = Booking(99, 2, 2, T(8), T(10), lecturer="Nguyễn Văn A")
    v = validate_assignment(req(1, lec="nguyễn văn a"), room(1, 50), [b])
    assert codes(v) == {V.LECTURER_TIME_CONFLICT}


def test_lecturer_unknown_is_skipped():
    b = Booking(99, 2, 2, T(8), T(10), lecturer=None)
    assert validate_assignment(req(1, lec=None), room(1, 50), [b]) == []


def test_multiple_violations_are_all_reported():
    v = validate_assignment(req(1, n=100, typ="lab", eq="loa"), room(1, 10), [])
    assert codes(v) == {V.ROOM_CAPACITY, V.ROOM_TYPE, V.ROOM_EQUIPMENT}


def test_invalid_data_reported():
    assert codes(validate_assignment(req(1, n=0), room(1, 50), [])) == {V.INVALID_DATA}
    assert codes(validate_assignment(req(1, wd=8), room(1, 50), [])) == {V.INVALID_DATA}
    assert codes(validate_assignment(req(1, s=T(10), e=T(9)), room(1, 50), [])) == {V.INVALID_DATA}


# ---------- đổi phòng thủ công dùng chung hàm validate ----------

def test_manual_move_ignores_own_current_booking():
    # Buổi 1 đang ở phòng 1; đổi sang chính phòng 1 (hoặc sửa giờ) không được tự xung đột.
    own = Booking(1, 1, 2, T(7), T(9, 30))
    assert validate_assignment(req(1), room(1, 50), [own], ignore_session_id=1) == []


def test_manual_move_into_occupied_room_is_rejected():
    other = Booking(5, 2, 2, T(7), T(9, 30))
    own = Booking(1, 1, 2, T(7), T(9, 30))
    v = validate_assignment(req(1), room(2, 50), [own, other], ignore_session_id=1)
    assert codes(v) == {V.ROOM_TIME_CONFLICT}


# ---------- allocate: best-fit ----------

def test_best_fit_picks_smallest_suitable_room():
    rooms = [room(1, 200), room(2, 60), room(3, 35), room(4, 40)]
    res = allocate([req(1, n=30)], rooms)
    assert res.assigned[0].room_id == 3
    assert res.assigned[0].wasted_seats == 5


def test_best_fit_skips_too_small_and_wrong_type():
    rooms = [room(1, 20), room(2, 45, typ="lab"), room(3, 50)]
    assert allocate([req(1, n=30)], rooms).assigned[0].room_id == 3


def test_hard_class_goes_first_so_scarce_room_is_not_wasted():
    # Phòng 1 (50 chỗ, có máy chiếu) là phòng duy nhất cho lớp cần máy chiếu.
    # Lớp dễ (không thiết bị) xếp trước theo mã sẽ chiếm phòng 1 nếu không ưu tiên độ khó.
    rooms = [room(1, 50, eq="máy chiếu"), room(2, 50)]
    easy = req(1, n=45, code="A-easy")
    hard = req(2, n=45, eq="máy chiếu", code="Z-hard")
    res = allocate([easy, hard], rooms)
    by = {p.session_id: p.room_id for p in res.assigned}
    assert by == {2: 1, 1: 2}
    assert not res.unassigned


def test_larger_class_prioritised_over_smaller():
    rooms = [room(1, 100), room(2, 40)]
    res = allocate([req(1, n=35), req(2, n=95, wd=2)], rooms)
    # Cùng khung giờ: lớp 95 phải vào phòng 100, lớp 35 vào phòng 40.
    by = {p.session_id: p.room_id for p in res.assigned}
    assert by == {2: 1, 1: 2}


def test_same_room_reused_in_non_overlapping_slots():
    rooms = [room(1, 50)]
    res = allocate([req(1, s=T(7), e=T(9)), req(2, s=T(9), e=T(11))], rooms)
    assert [p.room_id for p in res.assigned] == [1, 1]


def test_existing_bookings_are_respected():
    rooms = [room(1, 40), room(2, 60)]
    existing = [Booking(50, 1, 2, T(7), T(9, 30))]
    res = allocate([req(1, n=30)], rooms, existing)
    assert res.assigned[0].room_id == 2


# ---------- allocate: không xếp được + lý do ----------

def test_unassigned_not_enough_capacity_message():
    res = allocate([req(1, n=300)], [room(1, 100), room(2, 50)])
    assert not res.assigned
    r = res.unassigned[0].reasons[0]
    assert r.code == V.ROOM_CAPACITY and "100" in r.message and "300" in r.message


def test_unassigned_no_room_of_required_type():
    res = allocate([req(1, typ="lab")], [room(1, 50)])
    assert res.unassigned[0].reasons[0].code == V.ROOM_TYPE


def test_unassigned_missing_equipment():
    res = allocate([req(1, n=30, eq="máy chiếu")], [room(1, 50)])
    assert res.unassigned[0].reasons[0].code == V.ROOM_EQUIPMENT


def test_unassigned_all_suitable_rooms_busy():
    existing = [Booking(50, 1, 2, T(7), T(9, 30))]
    res = allocate([req(1, n=30)], [room(1, 50)], existing)
    r = res.unassigned[0].reasons[0]
    assert r.code == V.ROOM_TIME_CONFLICT and "1 phòng" in r.message


def test_unassigned_lecturer_busy_reports_lecturer_not_room():
    existing = [Booking(50, 9, 2, T(8), T(10), lecturer="GV A")]
    res = allocate([req(1, lec="GV A")], [room(1, 50)], existing)
    assert res.unassigned[0].reasons[0].code == V.LECTURER_TIME_CONFLICT


def test_two_classes_same_lecturer_same_time_second_fails():
    rooms = [room(1, 50), room(2, 50)]
    res = allocate([req(1, lec="GV A"), req(2, lec="GV A")], rooms)
    assert len(res.assigned) == 1 and len(res.unassigned) == 1
    assert res.unassigned[0].reasons[0].code == V.LECTURER_TIME_CONFLICT


def test_no_rooms_at_all():
    res = allocate([req(1)], [])
    assert res.unassigned[0].reasons[0].code == V.NO_ROOMS


def test_invalid_data_does_not_break_the_batch():
    res = allocate([req(1, n=0), req(2, s=T(10), e=T(9)), req(3)], [room(1, 50)])
    assert {i.session_id for i in res.invalid} == {1, 2}
    assert [p.session_id for p in res.assigned] == [3]


def test_empty_input():
    res = allocate([], [room(1, 50)])
    assert res.summary == {"total": 0, "assigned": 0, "unassigned": 0, "invalid": 0, "total_wasted_seats": 0}


# ---------- tính chất toàn cục ----------

def test_deterministic_regardless_of_input_order():
    rooms = [room(i, 30 + i * 5) for i in range(1, 6)]
    reqs = [req(i, n=25 + i, s=T(7 + i % 3), e=T(9 + i % 3)) for i in range(1, 9)]
    a = allocate(reqs, rooms)
    b = allocate(list(reversed(reqs)), list(reversed(rooms)))
    assert {(p.session_id, p.room_id) for p in a.assigned} == {(p.session_id, p.room_id) for p in b.assigned}


def test_every_placement_is_valid_under_shared_validator():
    """Thuật toán không bao giờ tạo ra kết quả mà validate chung bác bỏ."""
    import random

    rnd = random.Random(7)
    equips = ["", "máy chiếu", "máy chiếu, điều hòa"]
    rooms = [room(i, rnd.choice([30, 45, 60, 120]), eq=rnd.choice(equips)) for i in range(1, 9)]
    reqs = [
        req(
            i,
            n=rnd.randint(10, 110),
            wd=rnd.randint(1, 3),
            s=T(rnd.choice([7, 9, 13])),
            e=T(rnd.choice([10, 12, 16])),
            eq=rnd.choice(equips),
            lec=rnd.choice(["A", "B", "C", None]),
        )
        for i in range(1, 80)
    ]
    reqs = [r for r in reqs if r.end_time > r.start_time]
    res = allocate(reqs, rooms)
    by_id = {r.session_id: r for r in reqs}
    rooms_by_id = {r.id: r for r in rooms}
    placed = {p.session_id: p for p in res.assigned}
    bookings = [
        Booking(sid, p.room_id, by_id[sid].weekday, by_id[sid].start_time, by_id[sid].end_time, by_id[sid].lecturer)
        for sid, p in placed.items()
    ]
    for sid, p in placed.items():
        assert validate_assignment(by_id[sid], rooms_by_id[p.room_id], bookings, ignore_session_id=sid) == []
    assert len(placed) + len(res.unassigned) + len(res.invalid) == len(reqs)

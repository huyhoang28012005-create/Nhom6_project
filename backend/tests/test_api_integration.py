from __future__ import annotations

import os
from io import BytesIO

os.environ["AUTO_SEED"] = "false"

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from ops_router import seed_demo_dataset


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        seed_demo_dataset(db, reset=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def auth_header(client: TestClient, username: str, password: str = "123") -> dict[str, str]:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_rbac_4_roles(client: TestClient):
    # Chưa đăng nhập -> 401
    r = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
    )
    assert r.status_code == 401

    # Sinh viên -> không được tạo phòng (403)
    sv_h = auth_header(client, "sv_minhanh")
    r_sv = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
        headers=sv_h,
    )
    assert r_sv.status_code == 403

    # Giảng viên -> không được chạy auto allocation (403)
    gv_h = auth_header(client, "gv_an")
    assert client.post("/api/allocation/run", json={"apply": False}, headers=gv_h).status_code == 403

    # Cán bộ Đào tạo -> được tạo phòng nhưng không được xem danh sách tài khoản Admin (403)
    off_h = auth_header(client, "officer01")
    r_off = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
        headers=off_h,
    )
    assert r_off.status_code == 201
    assert client.get("/api/auth/users", headers=off_h).status_code == 403

    # Admin -> toàn quyền ADM-01 (xem, tạo, khóa/mở khóa, cấp lại mật khẩu)
    adm_h = auth_header(client, "admin")
    users_res = client.get("/api/auth/users", headers=adm_h)
    assert users_res.status_code == 200
    assert len(users_res.json()) >= 4

    new_u = client.post(
        "/api/auth/users",
        json={"username": "gv_moi", "password": "456", "full_name": "TS. Trần Bình", "role": "LECTURER"},
        headers=adm_h,
    )
    assert new_u.status_code == 201
    uid = new_u.json()["id"]

    # Khóa tài khoản -> đăng nhập bị 403
    client.patch(f"/api/auth/users/{uid}/toggle-active", headers=adm_h)
    assert client.post("/api/auth/login", json={"username": "gv_moi", "password": "456"}).status_code == 403


def test_delete_room_with_schedule_returns_409_not_500(client: TestClient):
    off_h = auth_header(client, "officer01")
    rooms = client.get("/api/rooms").json()
    b1_204 = next(r for r in rooms if r["room_code"] == "B1-204")
    res = client.delete(f"/api/rooms/{b1_204['id']}", headers=off_h)
    assert res.status_code == 409


def test_end_to_end_import_allocate_export_and_stats(client: TestClient):
    off_h = auth_header(client, "officer01")

    # 1. Import thêm 2 lớp từ file Excel chuẩn
    wb = Workbook()
    ws = wb.active
    ws.append(["class_code", "course_name", "lecturer", "student_count", "weekday", "shift", "room_code", "required_room_type", "required_equipment"])
    ws.append(["NEW-101", "Kiến trúc máy tính", "TS. Lê Hải", 42, "Thứ 6", "Ca 3", "", "classroom", "Máy chiếu"])
    ws.append(["NEW-LAB", "Thực hành Kiến trúc MT", "TS. Lê Hải", 38, 6, 3, "", "lab", "Máy tính"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    imp = client.post(
        "/api/timetable/import",
        files={"file": ("tkb_moi.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=off_h,
    )
    assert imp.status_code == 201, imp.text
    assert imp.json()["imported_count"] == 2

    # 2. Chạy Auto Allocation xem trước (apply=False) rồi áp dụng (apply=True)
    preview = client.post("/api/allocation/run", json={"apply": False}, headers=off_h)
    assert preview.status_code == 200
    assert preview.json()["applied"] is False
    assert preview.json()["summary"]["assigned"] >= 8

    apply_res = client.post("/api/allocation/run", json={"apply": True}, headers=off_h)
    assert apply_res.status_code == 200
    assert apply_res.json()["applied"] is True
    assert apply_res.json()["summary"]["unassigned"] == 0

    # 3. Xuất Excel & kiểm tra header Content-Disposition chuẩn
    exp = client.get("/api/timetable/export?fmt=xlsx", headers=off_h)
    assert exp.status_code == 200
    assert exp.headers["content-disposition"] == 'attachment; filename="CAMS_timetable_export.xlsx"'

    # 4. Thống kê Sprint 3 phản ánh 100% lớp đã gán phòng
    stats = client.get("/api/stats/overview", headers=off_h)
    assert stats.status_code == 200
    data = stats.json()
    assert data["assignment_rate"] == 100.0
    assert data["unassigned_sessions"] == 0


def test_collision_br01_capacity_br02_and_change_request_audit_br04(client: TestClient):
    off_h = auth_header(client, "officer01")
    gv_h = auth_header(client, "gv_an")

    sessions = client.get("/api/timetable/sessions").json()
    rooms = {r["room_code"]: r for r in client.get("/api/rooms").json()}

    # Tạo 1 buổi khác cùng Thứ 2 (weekday=1), 07:00-09:30 cố tình gán trùng vào B1-204 -> chặn cứng 409 (BR-01)
    classes = client.get("/api/classes").json()
    eng = next(c for c in classes if c["class_code"] == "ENG1001-03")
    collision = client.post(
        "/api/timetable/sessions",
        json={
            "class_id": eng["id"],
            "weekday": 1,
            "start_time": "07:00:00",
            "end_time": "09:30:00",
            "room_id": rooms["B1-204"]["id"],
        },
        headers=off_h,
    )
    assert collision.status_code == 409
    assert "B1-204" in collision.json()["detail"]

    # BR-02: Gán lớp MAT1101-05 (95 SV) vào A1-402 (70 chỗ) mặc định bị từ chối 409, nhưng allow_overload=true cho phép
    s_mat = next(s for s in sessions if s["room_id"] == rooms["B2-110"]["id"])
    overload_block = client.put(
        f"/api/timetable/sessions/{s_mat['id']}",
        json={**s_mat, "room_id": rooms["A1-402"]["id"]},
        headers=off_h,
    )
    assert overload_block.status_code == 409

    overload_ok = client.put(
        f"/api/timetable/sessions/{s_mat['id']}?allow_overload=true",
        json={**s_mat, "room_id": rooms["A1-402"]["id"]},
        headers=off_h,
    )
    assert overload_ok.status_code == 200

    # LEC-03 & OFF-07: Giảng viên gửi đơn xin đổi phòng -> Cán bộ Đào tạo duyệt -> Ghi Audit Log (BR-04)
    s_csdl = next(s for s in sessions if s["room_id"] == rooms["B1-204"]["id"])
    cr = client.post(
        "/api/change-requests",
        json={
            "session_id": s_csdl["id"],
            "requested_room_id": rooms["A2-305"]["id"],
            "reason": "Cần giảng đường lớn có micro cho buổi thuyết trình",
        },
        headers=gv_h,
    )
    assert cr.status_code == 201
    req_id = cr.json()["id"]

    rev = client.post(
        f"/api/change-requests/{req_id}/review",
        json={"action": "APPROVE"},
        headers=off_h,
    )
    assert rev.status_code == 200

    updated_s = client.get(f"/api/timetable/sessions/{s_csdl['id']}").json()
    assert updated_s["room_id"] == rooms["A2-305"]["id"]

    logs = client.get("/api/audit-logs", headers=off_h).json()
    assert any(lg["action"] == "APPROVE_CHANGE_REQUEST" for lg in logs)


def test_closure_dates_br03_and_student_lookup_stu01(client: TestClient):
    off_h = auth_header(client, "officer01")

    # Tra cứu lịch sinh viên công khai theo MSSV 21021234 (STU-01)
    stu = client.get("/api/lookup/timetable?student_code=21021234")
    assert stu.status_code == 200
    assert stu.json()["student"]["student_name"] == "Nguyễn Minh Anh"
    assert stu.json()["total"] >= 4

    # ADM-04: Final <= First bị từ chối 422
    bad_cfg = client.put(
        "/api/settings",
        json={"first_closure_date": "2026-12-20", "final_closure_date": "2026-12-10", "enforce_closure": True},
        headers=off_h,
    )
    assert bad_cfg.status_code == 422

    # BR-03: Đặt cả hai mốc về quá khứ -> Khóa Auto Allocation và khóa sửa phòng
    lock_cfg = client.put(
        "/api/settings",
        json={"first_closure_date": "2020-01-01", "final_closure_date": "2020-02-01", "enforce_closure": True},
        headers=off_h,
    )
    assert lock_cfg.status_code == 200

    assert client.post("/api/allocation/run", json={"apply": True}, headers=off_h).status_code == 403
def test_notifications_are_private_and_read_state_is_per_user(
    client: TestClient,
):
    # 1. Người chưa đăng nhập không được xem hoặc đánh dấu đã đọc
    assert client.get("/api/notifications").status_code == 401
    assert client.post("/api/notifications/read-all").status_code == 401

    # 2. Đăng nhập bằng hai tài khoản khác nhau
    student_headers = auth_header(client, "sv_minhanh")
    lecturer_headers = auth_header(client, "gv_an")

    # 3. Sinh viên xem được thông báo chung và thông báo riêng của mình
    student_res = client.get(
        "/api/notifications",
        headers=student_headers,
    )
    assert student_res.status_code == 200

    student_notifications = student_res.json()

    shared_message = "Cơ sở dữ liệu (INT2211-02)"
    private_message = "Yêu cầu mượn phòng TV-301"

    student_shared = next(
        n for n in student_notifications
        if shared_message in n["message"]
    )
    student_private = next(
        n for n in student_notifications
        if private_message in n["message"]
    )

    assert student_shared["is_unread"] is True
    assert student_private["is_unread"] is True

    # 4. Giảng viên không được xem thông báo riêng của sinh viên
    lecturer_res = client.get(
        "/api/notifications",
        headers=lecturer_headers,
    )
    assert lecturer_res.status_code == 200

    lecturer_notifications = lecturer_res.json()

    assert not any(
        private_message in n["message"]
        for n in lecturer_notifications
    )

    lecturer_shared = next(
        n for n in lecturer_notifications
        if shared_message in n["message"]
    )
    assert lecturer_shared["is_unread"] is True

    # 5. Sinh viên đánh dấu đã đọc thông báo của mình
    read_res = client.post(
        "/api/notifications/read-all",
        headers=student_headers,
    )
    assert read_res.status_code == 200

    student_after = client.get(
        "/api/notifications",
        headers=student_headers,
    ).json()

    student_shared_after = next(
        n for n in student_after
        if shared_message in n["message"]
    )
    assert student_shared_after["is_unread"] is False

    # 6. Trạng thái đọc của giảng viên không bị ảnh hưởng
    lecturer_after = client.get(
        "/api/notifications",
        headers=lecturer_headers,
    ).json()

    lecturer_shared_after = next(
        n for n in lecturer_after
        if shared_message in n["message"]
    )
    assert lecturer_shared_after["is_unread"] is True
def test_booking_history_is_private_by_user_role(client: TestClient):
    # 1. Người chưa đăng nhập không được xem lịch sử
    assert client.get("/api/bookings").status_code == 401

    # 2. Đăng nhập bằng bốn tài khoản
    student_headers = auth_header(client, "sv_minhanh")
    lecturer_headers = auth_header(client, "gv_an")
    officer_headers = auth_header(client, "officer01")
    admin_headers = auth_header(client, "admin")

    # 3. Chọn phòng có sức chứa lớn nhất
    rooms = client.get("/api/rooms").json()
    room = max(rooms, key=lambda r: r["capacity"])

    # 4. Sinh viên tạo một yêu cầu đặt phòng
    student_booking = client.post(
        "/api/bookings",
        headers=student_headers,
        json={
            "room_id": room["id"],
            "use_date": "2099-01-01",
            "shift_label": "TEST_STUDENT",
            "attendee_count": 2,
            "purpose": "Kiểm thử lịch sử đặt phòng sinh viên",
        },
    )
    assert student_booking.status_code == 201, student_booking.text
    student_booking_id = student_booking.json()["id"]

    # 5. Giảng viên tạo một yêu cầu đặt phòng khác
    lecturer_booking = client.post(
        "/api/bookings",
        headers=lecturer_headers,
        json={
            "room_id": room["id"],
            "use_date": "2099-01-02",
            "shift_label": "TEST_LECTURER",
            "attendee_count": 2,
            "purpose": "Kiểm thử lịch sử đặt phòng giảng viên",
        },
    )
    assert lecturer_booking.status_code == 201, lecturer_booking.text
    lecturer_booking_id = lecturer_booking.json()["id"]

    # 6. Sinh viên chỉ xem được yêu cầu của mình
    student_history = client.get(
        "/api/bookings",
        headers=student_headers,
    )
    assert student_history.status_code == 200

    student_ids = {b["id"] for b in student_history.json()}

    assert student_booking_id in student_ids
    assert lecturer_booking_id not in student_ids

    # 7. Giảng viên chỉ xem được yêu cầu của mình
    lecturer_history = client.get(
        "/api/bookings",
        headers=lecturer_headers,
    )
    assert lecturer_history.status_code == 200

    lecturer_ids = {b["id"] for b in lecturer_history.json()}

    assert lecturer_booking_id in lecturer_ids
    assert student_booking_id not in lecturer_ids

    # 8. Officer xem được cả hai yêu cầu
    officer_history = client.get(
        "/api/bookings",
        headers=officer_headers,
    )
    assert officer_history.status_code == 200

    officer_ids = {b["id"] for b in officer_history.json()}

    assert student_booking_id in officer_ids
    assert lecturer_booking_id in officer_ids

    # 9. Admin xem được cả hai yêu cầu
    admin_history = client.get(
        "/api/bookings",
        headers=admin_headers,
    )
    assert admin_history.status_code == 200

    admin_ids = {b["id"] for b in admin_history.json()}

    assert student_booking_id in admin_ids
    assert lecturer_booking_id in admin_ids
def test_change_request_list_is_private_by_user_role(client: TestClient):
    # 1. Người chưa đăng nhập không được xem đơn đổi phòng
    assert client.get("/api/change-requests").status_code == 401

    # 2. Đăng nhập các tài khoản
    admin_headers = auth_header(client, "admin")
    lecturer_headers = auth_header(client, "gv_an")
    student_headers = auth_header(client, "sv_minhanh")
    officer_headers = auth_header(client, "officer01")

    # 3. Tạo thêm một tài khoản giảng viên để kiểm tra quyền riêng tư
    create_other = client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={
            "username": "gv_other",
            "password": "123",
            "full_name": "Giảng viên khác",
            "role": "LECTURER",
        },
    )
    assert create_other.status_code in (200, 201), create_other.text

    other_lecturer_headers = auth_header(client, "gv_other")

    # 4. Chọn buổi học và phòng phù hợp
    sessions = client.get("/api/timetable/sessions").json()
    rooms = {
        r["room_code"]: r
        for r in client.get("/api/rooms").json()
    }

    session = next(
        s for s in sessions
        if s["room_id"] == rooms["B1-204"]["id"]
    )

    # 5. Giảng viên gửi đơn xin đổi phòng
    response = client.post(
        "/api/change-requests",
        headers=lecturer_headers,
        json={
            "session_id": session["id"],
            "requested_room_id": rooms["A2-305"]["id"],
            "reason": "Cần giảng đường lớn có micro cho buổi thuyết trình",
        },
    )

    assert response.status_code == 201, response.text
    request_id = response.json()["id"]

    # 6. Giảng viên gửi đơn chỉ xem được đơn của mình
    own_requests = client.get(
        "/api/change-requests",
        headers=lecturer_headers,
    )
    assert own_requests.status_code == 200

    own_ids = {item["id"] for item in own_requests.json()}
    assert request_id in own_ids

    # 7. Giảng viên khác không xem được đơn của người khác
    other_requests = client.get(
        "/api/change-requests",
        headers=other_lecturer_headers,
    )
    assert other_requests.status_code == 200

    other_ids = {item["id"] for item in other_requests.json()}
    assert request_id not in other_ids

    # 8. Sinh viên nhận danh sách rỗng
    student_requests = client.get(
        "/api/change-requests",
        headers=student_headers,
    )
    assert student_requests.status_code == 200
    assert student_requests.json() == []

    # 9. Officer xem được tất cả
    officer_requests = client.get(
        "/api/change-requests",
        headers=officer_headers,
    )
    assert officer_requests.status_code == 200
    assert request_id in {item["id"] for item in officer_requests.json()}

    # 10. Admin xem được tất cả
    admin_requests = client.get(
        "/api/change-requests",
        headers=admin_headers,
    )
    assert admin_requests.status_code == 200
    assert request_id in {item["id"] for item in admin_requests.json()}
def test_lecturer_cannot_request_room_change_for_another_lecturer(
    client: TestClient,
):
    lecturer_headers = auth_header(client, "gv_an")

    classes = client.get("/api/classes").json()
    sessions = client.get("/api/timetable/sessions").json()
    rooms = client.get("/api/rooms").json()

    class_by_id = {c["id"]: c for c in classes}

    # Tìm buổi học thuộc lớp do giảng viên khác phụ trách.
    other_session = next(
        s for s in sessions
        if class_by_id[s["class_id"]]["lecturer"]
        != "TS. Nguyễn Văn An"
    )

    target_room = next(
        r for r in rooms
        if r["id"] != other_session["room_id"]
    )

    response = client.post(
        "/api/change-requests",
        headers=lecturer_headers,
        json={
            "session_id": other_session["id"],
            "requested_room_id": target_room["id"],
            "reason": "Xin đổi phòng cho buổi học này",
        },
    )

    assert response.status_code == 403
    assert "không được phép" in response.json()["detail"].lower()
def test_issue_reporting_requires_login_and_uses_authenticated_reporter(
    client: TestClient,
):
    # 1. Người chưa đăng nhập không được xem hoặc gửi báo cáo
    assert client.get("/api/issues").status_code == 401

    anonymous_response = client.post(
        "/api/issues",
        json={
            "room_name": "A2-305",
            "issue_type": "Thiết bị",
            "description": "Máy chiếu không hoạt động bình thường",
        },
    )
    assert anonymous_response.status_code == 401

    # 2. Đăng nhập bằng sinh viên và giảng viên
    student_headers = auth_header(client, "sv_minhanh")
    lecturer_headers = auth_header(client, "gv_an")

    # 3. Sinh viên gửi báo cáo
    student_response = client.post(
        "/api/issues",
        headers=student_headers,
        json={
            "room_name": "A2-305",
            "issue_type": "Thiết bị",
            "description": "Máy chiếu phòng học không hoạt động",
            "reporter_name": "Tên giả mạo",
        },
    )
    assert student_response.status_code == 201, student_response.text
    student_issue_id = student_response.json()["id"]

    # 4. Giảng viên gửi báo cáo
    lecturer_response = client.post(
        "/api/issues",
        headers=lecturer_headers,
        json={
            "room_name": "B1-204",
            "issue_type": "Điều hòa / điện",
            "description": "Điều hòa phòng học phát ra tiếng ồn lớn",
        },
    )
    assert lecturer_response.status_code == 201, lecturer_response.text
    lecturer_issue_id = lecturer_response.json()["id"]

    # 5. Sinh viên xem danh sách và kiểm tra tên người báo cáo
    student_issues = client.get(
        "/api/issues",
        headers=student_headers,
    )
    assert student_issues.status_code == 200

    student_item = next(
        item for item in student_issues.json()
        if item["id"] == student_issue_id
    )
    assert student_item["reporter_name"] == "Nguyễn Minh Anh"

    # 6. Giảng viên cũng xem được danh sách sự cố
    lecturer_issues = client.get(
        "/api/issues",
        headers=lecturer_headers,
    )
    assert lecturer_issues.status_code == 200

    lecturer_item = next(
        item for item in lecturer_issues.json()
        if item["id"] == lecturer_issue_id
    )
    assert lecturer_item["reporter_name"] == "TS. Nguyễn Văn An"

    # 7. Cả hai tài khoản đều thấy được danh sách sự cố chung
    lecturer_visible_ids = {
        item["id"] for item in lecturer_issues.json()
    }
    assert student_issue_id in lecturer_visible_ids
def test_issue_status_update_requires_admin_or_officer(
    client: TestClient,
):
    student_headers = auth_header(client, "sv_minhanh")
    lecturer_headers = auth_header(client, "gv_an")
    officer_headers = auth_header(client, "officer01")
    admin_headers = auth_header(client, "admin")

    # Sinh viên tạo báo cáo sự cố
    created = client.post(
        "/api/issues",
        headers=student_headers,
        json={
            "room_name": "A2-305",
            "issue_type": "Thiết bị",
            "description": "Máy chiếu không hoạt động bình thường",
        },
    )
    assert created.status_code == 201

    issue_id = created.json()["id"]
    url = f"/api/issues/{issue_id}"

    # Người chưa đăng nhập không được cập nhật
    assert client.patch(
        url,
        json={"status": "IN_PROGRESS"},
    ).status_code == 401

    # Sinh viên và giảng viên không được cập nhật
    assert client.patch(
        url,
        headers=student_headers,
        json={"status": "IN_PROGRESS"},
    ).status_code == 403

    assert client.patch(
        url,
        headers=lecturer_headers,
        json={"status": "IN_PROGRESS"},
    ).status_code == 403

    # Officer được cập nhật
    officer_res = client.patch(
        url,
        headers=officer_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert officer_res.status_code == 200

    # Admin cũng được cập nhật
    admin_res = client.patch(
        url,
        headers=admin_headers,
        json={"status": "RESOLVED"},
    )
    assert admin_res.status_code == 200

    # Xác nhận trạng thái cuối cùng
    issues = client.get(
        "/api/issues",
        headers=student_headers,
    ).json()

    issue = next(x for x in issues if x["id"] == issue_id)
    assert issue["status"] == "RESOLVED"
/* CAMS Frontend API Client & Fallback Store (Đặng Huy Hoàng - Sprint 2 & Sprint 3) */

export type Role = "ADMIN" | "OFFICER" | "LECTURER" | "STUDENT";

export interface AuthUser {
  id: number;
  username: string;
  full_name: string;
  email?: string | null;
  role: Role;
  student_code?: string | null;
  department?: string | null;
  is_active: boolean;
}

export interface RoomItem {
  id: number;
  room_code: string;
  building: string;
  floor?: number | null;
  capacity: number;
  room_type: string;
  equipment?: string | null;
  notes?: string | null;
  is_available?: boolean;
  occupying_class?: string | null;
  busy_shifts?: number[];
}

export interface CourseClassItem {
  id: number;
  class_code: string;
  course_name: string;
  lecturer?: string | null;
  student_count: number;
  required_room_type: string;
  required_equipment?: string | null;
}

export interface EnrichedSession {
  id: number;
  class_id: number;
  class_code: string;
  course_name: string;
  lecturer: string;
  student_count: number;
  required_room_type: string;
  required_equipment: string;
  weekday: number;
  weekday_label: string;
  start_time: string;
  end_time: string;
  time_range: string;
  shift: number | null;
  shift_label: string;
  room_id: number | null;
  room_code: string | null;
  building: string | null;
  room_capacity: number | null;
  room_type: string | null;
  room_equipment: string | null;
  status: "ASSIGNED" | "UNASSIGNED" | "OVERLOADED";
  wasted_seats: number;
}

export interface AllocationRunResponse {
  applied: boolean;
  summary: {
    total: number;
    assigned: number;
    unassigned: number;
    invalid: number;
    total_wasted_seats: number;
  };
  assigned: Array<{
    session_id: number;
    class_code: string;
    room_id: number;
    room_code: string;
    wasted_seats: number;
  }>;
  unassigned: Array<{
    session_id: number;
    class_code: string;
    reasons: Array<{ code: string; message: string }>;
  }>;
  invalid: Array<{
    session_id: number;
    class_code: string;
    reasons: Array<{ code: string; message: string }>;
  }>;
}

export interface ChangeRequestItem {
  id: number;
  session_id: number;
  class_code: string;
  course_name: string;
  student_count: number;
  weekday: number;
  weekday_label: string;
  time_range: string;
  lecturer_name: string;
  old_room_id: number | null;
  old_room_code: string;
  requested_room_id: number;
  requested_room_code: string;
  requested_room_capacity: number;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  reject_reason?: string | null;
  reviewed_by?: string | null;
  created_at: string;
}

export interface BookingItem {
  id: number;
  room_id: number;
  room_code: string;
  room_label: string;
  requester_name: string;
  use_date: string;
  shift_label: string;
  attendee_count: number;
  purpose: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
}

export interface IssueItem {
  id: number;
  room_id?: number | null;
  room_name: string;
  reporter_name: string;
  issue_type: string;
  description: string;
  status: "RECEIVED" | "IN_PROGRESS" | "RESOLVED";
  created_at: string;
}

export interface NotificationItem {
  id: number;
  category: string;
  tone: "b" | "g" | "r" | "y";
  message: string;
  is_unread: boolean;
  created_at: string;
}

export interface AuditLogItem {
  id: number;
  actor_name: string;
  actor_role: string;
  action: string;
  target: string;
  old_value: string;
  new_value: string;
  reason: string;
  created_at: string;
}

export interface SystemSettingsData {
  semester_name: string;
  first_closure_date: string;
  final_closure_date: string;
  enforce_closure: boolean;
  today: string;
  is_past_first_closure: boolean;
  is_past_final_closure: boolean;
  days_until_first_closure: number;
  days_until_final_closure: number;
  shifts: Array<{
    shift_number: number;
    shift_name: string;
    period_range: string;
    start_time: string;
    end_time: string;
  }>;
}

export interface StatsOverview {
  total_rooms: number;
  total_classes: number;
  total_sessions: number;
  assigned_sessions: number;
  unassigned_sessions: number;
  assignment_rate: number;
  overloaded_sessions: number;
  total_wasted_seats: number;
  average_utilization_pct: number;
  pending_change_requests: number;
  pending_bookings: number;
  open_issues: number;
  by_room: Array<{
    room_id: number;
    room_code: string;
    building: string;
    room_type: string;
    capacity: number;
    sessions_count: number;
    utilization_pct: number;
    seat_fill_pct: number;
    wasted_seats: number;
  }>;
  by_building: Array<{
    building: string;
    room_count: number;
    sessions_count: number;
    total_capacity: number;
    utilization_pct: number;
  }>;
  by_weekday: Array<{
    weekday: number;
    label: string;
    total_sessions: number;
    assigned_sessions: number;
  }>;
}

function resolveApiRoot(): string {
  const env = import.meta.env as Record<string, string | undefined>;
  const raw = env.VITE_API_URL || env.VITE_API_BASE_URL || "http://localhost:8000";
  return raw.replace(/\/api\/?$/, "").replace(/\/+$/, "");
}

export const API_ROOT = resolveApiRoot();

const TOKEN_KEY = "cams_access_token";
const USER_KEY = "cams_current_user";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function saveAuthSession(token: string, user: AuthUser): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // Ignore storage quota errors in restricted iframes
  }
}

export function clearAuthSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // Ignore
  }
}

export class ApiError extends Error {
  status: number;
  errors?: Array<{ row: number; message: string }>;

  constructor(status: number, message: string, errors?: Array<{ row: number; message: string }>) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let msg = `Lỗi HTTP ${res.status}`;
    let rowErrors: Array<{ row: number; message: string }> | undefined;
    try {
      const payload = await res.json();
      if (typeof payload?.detail === "string") {
        msg = payload.detail;
      } else if (payload?.detail?.message) {
        msg = payload.detail.message;
        rowErrors = payload.detail.errors;
      } else if (Array.isArray(payload?.detail)) {
        msg = payload.detail.map((e: { msg?: string }) => e.msg || "").join("; ");
      }
    } catch {
      // Keep generic HTTP error
    }
    throw new ApiError(res.status, msg, rowErrors);
  }

  return (await res.json()) as T;
}

export async function checkBackendAlive(): Promise<boolean> {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), 2200);
  try {
    const res = await fetch(`${API_ROOT}/health`, { signal: ctrl.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timer);
  }
}

export async function downloadFromApi(path: string, fallbackFilename: string): Promise<void> {
  const token = getStoredToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_ROOT}${path}`, { headers });
  if (!res.ok) {
    let msg = `Không thể tải file (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") msg = data.detail;
    } catch {
      // Ignore
    }
    throw new ApiError(res.status, msg);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fallbackFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/* ===== Dữ liệu mẫu Fallback khi mở trên Figma Make Cloud (không có Backend local) ===== */
export const FALLBACK_USERS: Record<string, AuthUser> = {
  admin: { id: 1, username: "admin", full_name: "Quản trị viên Hệ thống", email: "admin@cams.edu.vn", role: "ADMIN", department: "Trung tâm CNTT", is_active: true },
  officer01: { id: 2, username: "officer01", full_name: "Lê Thu Trang", email: "daotao@cams.edu.vn", role: "OFFICER", department: "Phòng Đào tạo", is_active: true },
  gv_an: { id: 3, username: "gv_an", full_name: "TS. Nguyễn Văn An", email: "an.nv@cams.edu.vn", role: "LECTURER", department: "Khoa Công nghệ thông tin", is_active: true },
  sv_minhanh: { id: 4, username: "sv_minhanh", full_name: "Nguyễn Minh Anh", email: "minhanh@cams.edu.vn", role: "STUDENT", student_code: "21021234", department: "Khoa CNTT · K66-CNTT2", is_active: true },
};

export const FALLBACK_ROOMS: RoomItem[] = [
  { id: 1, room_code: "A2-305", building: "Tòa A2", floor: 3, capacity: 200, room_type: "hall", equipment: "Máy chiếu, Điều hòa, Micro, Loa, Wi-Fi, Ổ cắm", is_available: true, busy_shifts: [1] },
  { id: 2, room_code: "B1-204", building: "Tòa B1", floor: 2, capacity: 60, room_type: "classroom", equipment: "Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", is_available: false, occupying_class: "INT2211-02", busy_shifts: [1, 2] },
  { id: 3, room_code: "C3-101", building: "Tòa C3", floor: 1, capacity: 45, room_type: "lab", equipment: "Máy tính, Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", is_available: true, busy_shifts: [3] },
  { id: 4, room_code: "A1-402", building: "Tòa A1", floor: 4, capacity: 70, room_type: "classroom", equipment: "Máy chiếu, Điều hòa, Wi-Fi, Ổ cắm", is_available: true, busy_shifts: [2] },
  { id: 5, room_code: "B2-110", building: "Tòa B2", floor: 1, capacity: 120, room_type: "hall", equipment: "Máy chiếu, Điều hòa, Micro, Wi-Fi", is_available: true, busy_shifts: [2] },
  { id: 6, room_code: "TV-12", building: "Thư viện", floor: 2, capacity: 15, room_type: "group", equipment: "Điều hòa, Wi-Fi, Ổ cắm", is_available: true, busy_shifts: [] },
];

export const FALLBACK_SESSIONS: EnrichedSession[] = [
  { id: 1, class_id: 1, class_code: "INT2211-02", course_name: "Cơ sở dữ liệu", lecturer: "TS. Nguyễn Văn An", student_count: 58, required_room_type: "classroom", required_equipment: "Máy chiếu, Điều hòa", weekday: 1, weekday_label: "Thứ 2", start_time: "07:00:00", end_time: "09:30:00", time_range: "07:00 – 09:30", shift: 1, shift_label: "Ca 1", room_id: 2, room_code: "B1-204", building: "Tòa B1", room_capacity: 60, room_type: "classroom", room_equipment: "Máy chiếu, Điều hòa", status: "ASSIGNED", wasted_seats: 2 },
  { id: 2, class_id: 2, class_code: "MAT1101-05", course_name: "Giải tích 2", lecturer: "PGS. Trần Thị Mai", student_count: 95, required_room_type: "hall", required_equipment: "Máy chiếu, Micro", weekday: 1, weekday_label: "Thứ 2", start_time: "09:45:00", end_time: "12:00:00", time_range: "09:45 – 12:00", shift: 2, shift_label: "Ca 2", room_id: 5, room_code: "B2-110", building: "Tòa B2", room_capacity: 120, room_type: "hall", room_equipment: "Máy chiếu, Micro", status: "ASSIGNED", wasted_seats: 25 },
  { id: 3, class_id: 3, class_code: "INT3304-01", course_name: "Thực hành Mạng máy tính", lecturer: "ThS. Lê Hoàng Nam", student_count: 40, required_room_type: "lab", required_equipment: "Máy tính, Máy chiếu", weekday: 1, weekday_label: "Thứ 2", start_time: "13:00:00", end_time: "15:30:00", time_range: "13:00 – 15:30", shift: 3, shift_label: "Ca 3", room_id: 3, room_code: "C3-101", building: "Tòa C3", room_capacity: 45, room_type: "lab", room_equipment: "Máy tính, Máy chiếu", status: "ASSIGNED", wasted_seats: 5 },
  { id: 4, class_id: 4, class_code: "INT3401-01", course_name: "Trí tuệ nhân tạo", lecturer: "TS. Nguyễn Văn An", student_count: 65, required_room_type: "classroom", required_equipment: "Máy chiếu, Điều hòa", weekday: 2, weekday_label: "Thứ 3", start_time: "09:45:00", end_time: "12:00:00", time_range: "09:45 – 12:00", shift: 2, shift_label: "Ca 2", room_id: null, room_code: null, building: null, room_capacity: null, room_type: null, room_equipment: null, status: "UNASSIGNED", wasted_seats: 0 },
  { id: 5, class_id: 5, class_code: "PHY1100-01", course_name: "Vật lý đại cương", lecturer: "PGS. Hoàng Quốc Bảo", student_count: 150, required_room_type: "hall", required_equipment: "Máy chiếu, Micro", weekday: 3, weekday_label: "Thứ 4", start_time: "07:00:00", end_time: "09:30:00", time_range: "07:00 – 09:30", shift: 1, shift_label: "Ca 1", room_id: null, room_code: null, building: null, room_capacity: null, room_type: null, room_equipment: null, status: "UNASSIGNED", wasted_seats: 0 },
];

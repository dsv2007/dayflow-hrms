// API Service for integrating React Frontend with Odoo REST Controller
// Since Vite config sets a proxy for '/api' -> 'http://localhost:8079', we can use relative paths.

export interface EmployeeInfo {
  id: number;
  name: string;
  role: 'employee' | 'hr' | 'admin';
}

export interface UserSession {
  session_id: string;
  uid: number;
  username: string;
  employee: EmployeeInfo;
}

export interface AttendanceRecord {
  id: number;
  employee_name: string;
  date: string;
  check_in: string;
  check_out: string | null;
  worked_hours: number;
  status: 'present' | 'absent' | 'leave';
  remarks: string | null;
}

export interface LeaveRequest {
  id: number;
  employee_name: string;
  leave_type: 'sick' | 'casual' | 'earned';
  start_date: string;
  end_date: string;
  state: 'draft' | 'pending' | 'approved' | 'rejected';
  approver_name: string | null;
  approval_date: string | null;
  rejection_reason: string | null;
}

export interface PayrollRecord {
  id: number;
  employee_name: string;
  payroll_month: string;
  payroll_year: string;
  basic_salary: number;
  allowances: number;
  deductions: number;
  net_salary: number;
  state: 'draft' | 'approved' | 'paid';
}

export interface AIInsights {
  late_arrivals_html: string;
  overlapping_leaves_html: string;
  department_trends_html: string;
}

// Global fetch wrapper to handle request headers and responses cleanly
async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { error: text || 'Invalid JSON response from server' };
  }

  if (!response.ok) {
    throw new Error(data.error || `HTTP error! status: ${response.status}`);
  }

  return data as T;
}

interface OdooAuthResponse {
  uid: number;
  name: string;
  email: string;
  role: 'employee' | 'hr_officer' | 'admin';
  employee_id: number;
  department: string;
  session_id: string;
}

const mapOdooResponse = (res: OdooAuthResponse): UserSession => {
  return {
    session_id: res.session_id,
    uid: res.uid,
    username: res.email,
    employee: {
      id: res.employee_id,
      name: res.name,
      role: res.role === 'hr_officer' ? 'hr' : res.role,
    }
  };
};

export const api = {
  // Authentication
  async login(loginVal: string, passwordVal: string): Promise<UserSession> {
    const res = await apiFetch<OdooAuthResponse>('/api/login', {
      method: 'POST',
      body: JSON.stringify({ login: loginVal, password: passwordVal }),
    });
    return mapOdooResponse(res);
  },

  async signup(nameVal: string, loginVal: string, passwordVal: string, roleVal: 'employee' | 'hr_officer' | 'admin'): Promise<UserSession> {
    const res = await apiFetch<OdooAuthResponse>('/api/signup', {
      method: 'POST',
      body: JSON.stringify({ name: nameVal, login: loginVal, password: passwordVal, role: roleVal }),
    });
    return mapOdooResponse(res);
  },

  async logout(): Promise<{ message: string }> {
    return apiFetch<{ message: string }>('/api/logout', {
      method: 'POST',
    });
  },

  // Attendance
  async getAttendance(): Promise<AttendanceRecord[]> {
    return apiFetch<AttendanceRecord[]>('/api/attendance');
  },

  async checkIn(remarksVal?: string): Promise<{ message: string; attendance_id: number }> {
    return apiFetch<{ message: string; attendance_id: number }>('/api/attendance/check-in', {
      method: 'POST',
      body: JSON.stringify({ remarks: remarksVal || '' }),
    });
  },

  async checkOut(remarksVal?: string): Promise<{ message: string; worked_hours: number }> {
    return apiFetch<{ message: string; worked_hours: number }>('/api/attendance/check-out', {
      method: 'POST',
      body: JSON.stringify({ remarks: remarksVal || '' }),
    });
  },

  // Leave Management
  async getLeaves(): Promise<LeaveRequest[]> {
    return apiFetch<LeaveRequest[]>('/api/leaves');
  },

  async submitLeave(typeVal: 'sick' | 'casual' | 'earned', startDate: string, endDate: string): Promise<{ message: string; leave_id: number }> {
    return apiFetch<{ message: string; leave_id: number }>('/api/leave/submit', {
      method: 'POST',
      body: JSON.stringify({ leave_type: typeVal, start_date: startDate, end_date: endDate }),
    });
  },

  async approveLeave(leaveId: number): Promise<{ message: string }> {
    return apiFetch<{ message: string }>(`/api/leave/${leaveId}/approve`, {
      method: 'POST',
    });
  },

  async rejectLeave(leaveId: number, reasonVal: string): Promise<{ message: string }> {
    return apiFetch<{ message: string }>(`/api/leave/${leaveId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason: reasonVal }),
    });
  },

  // Payroll
  async getPayroll(): Promise<PayrollRecord[]> {
    return apiFetch<PayrollRecord[]>('/api/payroll');
  },

  // Deterministic AI Insights
  async getAIInsights(): Promise<AIInsights> {
    return apiFetch<AIInsights>('/api/ai-insights');
  },
};

# Dayflow HRMS - Next-Generation HR Management System

Dayflow HRMS is a modern, high-performance Human Resource Management System built for the Odoo Hackathon. It features a lightweight **React 19 Frontend Web Dashboard** and a robust **Odoo 19 Backend Addon** acting as the secure transactional core database and REST API.

---

## 🚀 Key Features

* **Biometric-Ready Attendance**: Secure Check-In / Check-Out validation constraints at the ORM layer preventing duplicate check-ins or checkout-without-checkin anomalies.
* **Smart Time-Off (Leave)**: Real-time overlapping date validations, department level density checks, and automatic cascade updates marking days as "Leave" upon approval.
* **Auto-Payroll calculation**: Dynamic net-salary calculations (`basic + allowances - deductions`) stored securely and backed by PostgreSQL database unique constraints preventing duplicate monthly payslips.
* **AI HR Insights & Warnings**: Pre-calculated manager intelligence signals exposing department-wide overlaps, high employee turnover hazards, late check-in metrics, and active employee rates.
* **Role-Based Security**: Rigorous privilege-based groups and record rules ensuring regular employees only view/edit their own logs while HR and admins have department/company scopes.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Client Application (React 19 / Vite)
        React[React Dashboard UI]
        ClientService[services/api.ts Client]
    end

    subgraph Server Application (Odoo 19 Core)
        APIControllers[REST HTTP API Controllers]
        OdooORM[Odoo ORM Validation Rules]
        OdooSecurity[Groups, ACLs, & Record Rules]
    end

    subgraph Database Layer (PostgreSQL)
        Postgres[(PostgreSQL: dayflow db)]
    end

    React -->|Interactions| ClientService
    ClientService -->|REST Calls / CORS Proxy| APIControllers
    APIControllers -->|Read/Write Operations| OdooORM
    OdooORM -->|Enforce Access Controls| OdooSecurity
    OdooSecurity -->|Queries & Updates| Postgres
```

---

## 📊 Database Schema (Odoo Models)

### 1. Extended Employee (`hr.employee` inherit)
* `dayflow_role`: `Selection` (`'employee'`, `'hr_officer'`, `'admin'`). Source-of-truth authorization check.
* `joining_date`: `Date` representing joining timestamp.

### 2. Attendance Log (`dayflow.attendance`)
* `employee_id`: `Many2one` reference to `hr.employee`.
* `date`: `Date` of logging (default: today).
* `check_in`: `Datetime` check-in timestamp.
* `check_out`: `Datetime` check-out timestamp.
* `worked_hours`: `Float` calculated automatically: `(check_out - check_in).total_seconds() / 3600.0`.
* `status`: `Selection` (`'present'`, `'absent'`, `'half_day'`, `'leave'`).

### 3. Leave Request (`dayflow.leave`)
* `employee_id`: `Many2one` reference to `hr.employee`.
* `leave_type`: `Selection` (`'sick'`, `'casual'`, `'earned'`).
* `start_date`: `Date` time-off start.
* `end_date`: `Date` time-off end.
* `state`: `Selection` (`'draft'`, `'pending'`, `'approved'`, `'rejected'`).
* `approver_id`: `Many2one` reference to approving `hr.employee`.

### 4. Payroll Records (`dayflow.payroll`)
* `employee_id`: `Many2one` reference to `hr.employee`.
* `payroll_month`: `Selection` representing month.
* `payroll_year`: `Char` representing year.
* `basic_salary`: `Float` base compensation.
* `allowances`: `Float` extra income.
* `deductions`: `Float` taxes or unpaid leaves.
* `net_salary`: `Float` calculated: `basic_salary + allowances - deductions`.

---

## 🔒 Security Matrix & Controls

Authorization is enforced at the Odoo backend server layer through security XML, ACLs, and row-level rules:

| Privilege Group | Models Accessible | Row-Level Access (Record Rules) |
|---|---|---|
| **Dayflow Employee** | `dayflow.attendance`, `dayflow.leave`, `dayflow.payroll` | **Self Only**: `[('employee_id.user_id', '=', user.id)]` |
| **Dayflow HR Officer** | All Dayflow Models | **All records** (Read/Write for approvals & payroll logs) |
| **Dayflow Administrator** | All Dayflow Models | **Full Root CRUD** (All records, settings, and metadata) |

---

## 🔌 API Controllers Reference

Authentication is session-cookie based (hashes validated against Odoo `res.users`).

| Endpoint | Method | Payload / Parameters | Access Group | Description |
|---|---|---|---|---|
| `/api/login` | `POST` | `{"login": "...", "password": "..."}` | Public | Authenticates and returns employee session metadata. |
| `/api/attendance/status` | `GET` | None | Employee | Fetch active check-in logs and recent logs. |
| `/api/attendance/check-in` | `POST` | `{"remarks": "..."}` | Employee | Log check-in time (validates no current check-in). |
| `/api/attendance/check-out`| `POST` | `{"remarks": "..."}` | Employee | Log check-out time (calculates worked hours). |
| `/api/leaves` | `GET` | None | Employee/HR | Retrieve time-off lists. HR gets all, employees get self. |
| `/api/leave/submit` | `POST` | `{"leave_type": "...", "start_date": "...", "end_date": "..."}` | Employee | Submit leave request (validates no date overlap). |
| `/api/leave/<id>/approve` | `POST` | None | HR Officer | Approve leave request (cascades status to attendance). |
| `/api/leave/<id>/reject` | `POST` | `{"rejection_reason": "..."}` | HR Officer | Reject leave request with a detailed log. |
| `/api/payroll` | `GET` | None | Employee/HR | Fetch payslips. HR gets company-wide logs, employees get self. |
| `/api/ai-insights` | `GET` | None | HR Officer/Admin | Fetch deterministic ML-style signals and warnings. |

---

## 🚀 Installation & Local Running Guide

### Prerequisite Checklist
* Odoo 19 installed locally (Windows Service stopped or configured to port 8079).
* PostgreSQL 16+ active on port 5432.
* Node.js 18+ and npm installed.

### Step 1: Start Odoo Backend Server (Port 8079)
Run the following from your terminal to launch Odoo with the custom Dayflow addon:
```powershell
& "C:\Program Files\Odoo 19.0.20260711\python\python.exe" "C:\Program Files\Odoo 19.0.20260711\server\odoo-bin" -c "C:\Program Files\Odoo 19.0.20260711\server\odoo.conf" --addons-path="C:\Program Files\Odoo 19.0.20260711\server\odoo\addons,C:\Users\SRCE\.gemini\antigravity\scratch" -d dayflow --db_user=odoo --db_password=odoopwd --http-port=8079
```

### Step 2: Start React Frontend Web Dashboard (Port 5173)
Open a separate shell, navigate to the web directory, and run the development server:
```powershell
cd dayflow-web
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

#### Demo Sign-In Credentials
* **Administrator**: Login: `admin` | Password: `admin`
* **HR Officer**: Login: `hr_user` | Password: `hrpwd`
* **Employee**: Login: `emp_user` | Password: `emppwd`

---

## 🧪 Running Backend Unit Tests

A comprehensive transaction test suite is included to verify business logic and constraint boundaries:
```powershell
& "C:\Program Files\Odoo 19.0.20260711\python\python.exe" "C:\Program Files\Odoo 19.0.20260711\server\odoo-bin" -c "C:\Program Files\Odoo 19.0.20260711\server\odoo.conf" --addons-path="C:\Program Files\Odoo 19.0.20260711\server\odoo\addons,C:\Users\SRCE\.gemini\antigravity\scratch" --http-port=8079 -d dayflow -u dayflow --db_user=odoo --db_password=odoopwd --test-enable --stop-after-init
```
*(Runs 6 test scenarios covering attendance sequences, overlapping leaves, and payroll uniqueness constraints).*

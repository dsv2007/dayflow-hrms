# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

def parse_json():
    try:
        return json.loads(request.httprequest.data.decode('utf-8'))
    except Exception:
        return {}

def json_response(data, status=200):
    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', 'http://localhost:5173'),
        ('Access-Control-Allow-Credentials', 'true'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With'),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS'),
    ]
    return request.make_response(
        json.dumps(data, default=str),
        headers=headers,
        status=status
    )

class DayflowAPIController(http.Controller):

    @http.route('/api/<path:subpath>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def api_cors_options(self, subpath=None, **kw):
        """Handle CORS pre-flight requests."""
        return json_response({}, status=200)

    @http.route('/api/login', type='http', auth='none', methods=['POST'], csrf=False)
    def api_login(self, **kw):
        """Authenticate user and return session and role details."""
        params = parse_json()
        db = params.get('db') or request.db or 'dayflow'
        login = params.get('email') or params.get('login')
        password = params.get('password')

        if not db or not login or not password:
            return json_response({'error': 'Missing credentials or database name.'}, status=400)

        try:
            auth_info = request.session.authenticate(request.env, {'type': 'password', 'login': login, 'password': password})
            uid = auth_info['uid']
            if not uid:
                return json_response({'error': 'Authentication failed.'}, status=401)
            
            # Fetch user and employee info
            user = request.env['res.users'].browse(uid)
            employee = user.employee_id
            
            if not employee:
                return json_response({'error': 'No employee record linked to this user account.'}, status=403)

            # Determine role from employee card
            role = employee.dayflow_role or 'employee'
            
            return json_response({
                'uid': uid,
                'name': employee.name,
                'email': employee.work_email or user.login,
                'role': role,
                'employee_id': employee.id,
                'department': employee.department_id.name or 'Unassigned',
                'session_id': request.session.sid
            })
        except Exception as e:
            _logger.exception("Authentication error")
            return json_response({'error': str(e)}, status=401)

    @http.route('/api/load-demo-data', type='http', auth='none', methods=['POST'], csrf=False)
    def api_load_demo_data(self, **kw):
        """Pre-populate the database with demo users, employees, attendances, leaves, and payrolls."""
        try:
            env = request.env(su=True)
            db_name = 'dayflow'
            
            # 1. Fetch default company
            company = env['res.company'].search([], limit=1)
            company_id = company.id if company else 1

            # 2. Setup standard departments if missing (Engineering, HR)
            dept_eng = env['hr.department'].search([('name', '=', 'Engineering')], limit=1)
            if not dept_eng:
                dept_eng = env['hr.department'].create({'name': 'Engineering'})
            
            dept_hr = env['hr.department'].search([('name', '=', 'Human Resources')], limit=1)
            if not dept_hr:
                dept_hr = env['hr.department'].create({'name': 'Human Resources'})

            # 3. Define the demo users schema
            demo_users_data = [
                {
                    'login': 'admin',
                    'name': 'Dayflow Admin',
                    'password': 'admin',
                    'role': 'admin',
                    'group': 'dayflow.group_dayflow_admin',
                    'dept': dept_eng.id
                },
                {
                    'login': 'hr_user',
                    'name': 'Sarah HR Manager',
                    'password': 'hrpwd',
                    'role': 'hr_officer',
                    'group': 'dayflow.group_dayflow_hr',
                    'dept': dept_hr.id
                },
                {
                    'login': 'emp_user',
                    'name': 'Alex Developer',
                    'password': 'emppwd',
                    'role': 'employee',
                    'group': 'dayflow.group_dayflow_employee',
                    'dept': dept_eng.id
                }
            ]

            # 4. Create/Get the users and employees
            created_employees = {}
            for u_data in demo_users_data:
                user = env['res.users'].search([('login', '=', u_data['login'])], limit=1)
                group = env.ref(u_data['group'])
                
                if not user:
                    user = env['res.users'].create({
                        'name': u_data['name'],
                        'login': u_data['login'],
                        'password': u_data['password'],
                        'company_id': company_id,
                        'company_ids': [(6, 0, [company_id])]
                    })
                
                # Assign groups safely
                user.write({'group_ids': [(4, group.id)]})
                if u_data['login'] == 'admin':
                    # Add base.group_system to admin user
                    sys_group = env.ref('base.group_system')
                    user.write({'group_ids': [(4, sys_group.id)]})

                # Check if employee card exists
                employee = env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                if not employee:
                    employee = env['hr.employee'].create({
                        'name': u_data['name'],
                        'work_email': u_data['login'] if '@' in u_data['login'] else f"{u_data['login']}@dayflow.com",
                        'user_id': user.id,
                        'company_id': company_id,
                        'department_id': u_data['dept'],
                        'dayflow_role': u_data['role']
                    })
                created_employees[u_data['role']] = employee

            # Clear existing data to allow clean re-loading
            env['dayflow.attendance'].search([]).unlink()
            env['dayflow.leave'].search([]).unlink()
            env['dayflow.payroll'].search([]).unlink()

            # 5. Generate historical attendances for last 30 days
            today = fields.Date.today()
            for i in range(30):
                date_val = today - timedelta(days=i)
                # Skip weekends
                if date_val.weekday() >= 5:
                    continue
                
                for role_name, emp in created_employees.items():
                    # Admin is always present on time (09:00 AM)
                    # Employee (Alex) arrives late on some days to trigger AI late arrival alert
                    is_late = (role_name == 'employee' and (i % 4 == 0)) # Arrived late every 4th day
                    
                    check_in_hour = 9 if is_late else 8
                    check_in_min = 30 if is_late else 45
                    
                    check_in_dt = datetime.combine(date_val, datetime.min.time()) + timedelta(hours=check_in_hour, minutes=check_in_min)
                    check_out_dt = check_in_dt + timedelta(hours=8, minutes=15)
                    
                    env['dayflow.attendance'].create({
                        'employee_id': emp.id,
                        'check_in': check_in_dt,
                        'check_out': check_out_dt,
                        'status': 'present'
                    })

            # 6. Generate overlapping leaves to trigger AI concurrency warning
            next_monday = today + timedelta(days=(7 - today.weekday()))
            
            # Alex Leave
            env['dayflow.leave'].create({
                'employee_id': created_employees['employee'].id,
                'leave_type': 'sick',
                'start_date': next_monday,
                'end_date': next_monday + timedelta(days=2),
                'state': 'approved',
                'approver_comments': 'Approved medical checkup.'
            })

            # Admin Leave (overlapping on Tuesday and Wednesday)
            env['dayflow.leave'].create({
                'employee_id': created_employees['admin'].id,
                'leave_type': 'casual',
                'start_date': next_monday + timedelta(days=1),
                'end_date': next_monday + timedelta(days=3),
                'state': 'pending',
                'approver_comments': 'Pending review.'
            })

            # 7. Generate payroll records for current and last month
            this_month_start = today.replace(day=1)
            last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
            
            for m_start in [last_month_start, this_month_start]:
                for role_name, emp in created_employees.items():
                    basic_salary = 8500 if role_name == 'admin' else (6000 if role_name == 'hr_officer' else 4500)
                    env['dayflow.payroll'].create({
                        'employee_id': emp.id,
                        'basic_salary': basic_salary,
                        'allowances': 500,
                        'deductions': 150,
                        'payroll_month': str(m_start.month).zfill(2),
                        'payroll_year': str(m_start.year),
                        'state': 'approved' if m_start == last_month_start else 'draft'
                    })

            return json_response({'message': 'Demo data loaded successfully!'})
        except Exception as e:
            _logger.exception("Load demo data error")
            return json_response({'error': str(e)}, status=500)

    @http.route('/api/signup', type='http', auth='none', methods=['POST'], csrf=False)
    def api_signup(self, **kw):
        """Sign up a new user and link them to an employee record."""
        params = parse_json()
        name = params.get('name')
        email = params.get('email') or params.get('login')
        password = params.get('password')
        role = params.get('role') or 'employee'
        db_name = params.get('db') or request.db or 'dayflow'

        if not name or not email or not password:
            return json_response({'error': 'Name, email, and password are required.'}, status=400)

        if role not in ['employee', 'hr_officer', 'admin']:
            return json_response({'error': 'Invalid role specified.'}, status=400)

        try:
            env = request.env(su=True)

            existing_user = env['res.users'].search([('login', '=', email)], limit=1)
            if existing_user:
                return json_response({'error': 'User with this email already exists.'}, status=409)

            group_ref = 'dayflow.group_dayflow_employee'
            if role == 'hr_officer':
                group_ref = 'dayflow.group_dayflow_hr'
            elif role == 'admin':
                group_ref = 'dayflow.group_dayflow_admin'

            group = env.ref(group_ref)
            if not group:
                return json_response({'error': f'Security group {group_ref} not found.'}, status=500)

            # Fetch default company
            company = env['res.company'].search([], limit=1)
            company_id = company.id if company else 1

            user_vals = {
                'name': name,
                'login': email,
                'password': password,
                'company_id': company_id,
                'company_ids': [(6, 0, [company_id])],
            }
            new_user = env['res.users'].create(user_vals)
            new_user.write({'group_ids': [(4, group.id)]})

            employee_vals = {
                'name': name,
                'work_email': email,
                'user_id': new_user.id,
                'company_id': company_id,
                'dayflow_role': role,
            }
            new_employee = env['hr.employee'].create(employee_vals)

            auth_info = request.session.authenticate(request.env, {'type': 'password', 'login': email, 'password': password})
            uid = auth_info['uid']

            return json_response({
                'uid': uid,
                'name': new_employee.name,
                'email': new_employee.work_email or new_user.login,
                'role': role,
                'employee_id': new_employee.id,
                'department': 'Unassigned',
                'session_id': request.session.sid
            })
        except Exception as e:
            _logger.exception("Signup error")
            return json_response({'error': str(e)}, status=500)

    @http.route('/api/logout', type='http', auth='user', methods=['POST'], csrf=False)
    def api_logout(self, **kw):
        """Clear user session."""
        request.session.logout()
        return json_response({'message': 'Successfully logged out.'})

    @http.route('/api/attendance', type='http', auth='user', methods=['GET'], csrf=False)
    def api_get_attendance(self, **kw):
        """Fetch attendance records. Employee record rules will automatically scope search."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)
        
        domain = []
        # If regular employee, restrict to own records (redundant but double safe)
        if employee.dayflow_role == 'employee':
            domain = [('employee_id', '=', employee.id)]
            
        attendances = request.env['dayflow.attendance'].search(domain)
        result = []
        for att in attendances:
            result.append({
                'id': att.id,
                'employee_name': att.employee_id.name,
                'date': att.date,
                'check_in': att.check_in,
                'check_out': att.check_out,
                'worked_hours': round(att.worked_hours, 2),
                'status': att.status,
                'remarks': att.remarks
            })
        return json_response(result)

    @http.route('/api/attendance/check-in', type='http', auth='user', methods=['POST'], csrf=False)
    def api_check_in(self, **kw):
        """Perform Check-In."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)
        
        try:
            attendance = request.env['dayflow.attendance'].action_check_in(employee.id)
            return json_response({
                'message': 'Checked in successfully.',
                'id': attendance.id,
                'check_in': attendance.check_in,
                'status': attendance.status
            })
        except Exception as e:
            return json_response({'error': str(e)}, status=400)

    @http.route('/api/attendance/check-out', type='http', auth='user', methods=['POST'], csrf=False)
    def api_check_out(self, **kw):
        """Perform Check-Out."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)
        
        try:
            attendance = request.env['dayflow.attendance'].action_check_out(employee.id)
            return json_response({
                'message': 'Checked out successfully.',
                'id': attendance.id,
                'check_in': attendance.check_in,
                'check_out': attendance.check_out,
                'worked_hours': round(attendance.worked_hours, 2)
            })
        except Exception as e:
            return json_response({'error': str(e)}, status=400)

    @http.route('/api/leaves', type='http', auth='user', methods=['GET'], csrf=False)
    def api_get_leaves(self, **kw):
        """GET list of leaves."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)

        domain = []
        if employee.dayflow_role == 'employee':
            domain = [('employee_id', '=', employee.id)]
        leaves = request.env['dayflow.leave'].search(domain)
        result = []
        for lv in leaves:
            result.append({
                'id': lv.id,
                'employee_name': lv.employee_id.name,
                'leave_type': lv.leave_type,
                'start_date': lv.start_date,
                'end_date': lv.end_date,
                'state': lv.state,
                'rejection_reason': lv.rejection_reason,
                'approver_comments': lv.approver_comments
            })
        return json_response(result)

    @http.route('/api/leave/submit', type='http', auth='user', methods=['POST'], csrf=False)
    def api_submit_leave(self, **kw):
        """POST a new leave request."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)

        params = parse_json()
        try:
            leave = request.env['dayflow.leave'].create({
                'employee_id': employee.id,
                'leave_type': params.get('leave_type', 'sick'),
                'start_date': fields.Date.from_string(params.get('start_date')),
                'end_date': fields.Date.from_string(params.get('end_date')),
                'approver_comments': params.get('remarks')
            })
            return json_response({
                'message': 'Leave request submitted successfully.',
                'id': leave.id,
                'state': leave.state
            })
        except Exception as e:
            return json_response({'error': str(e)}, status=400)

    @http.route('/api/leave/<int:leave_id>/approve', type='http', auth='user', methods=['POST'], csrf=False)
    def api_approve_leave(self, leave_id, **kw):
        """Approve a leave request (HR Officer only)."""
        employee = request.env.user.employee_id
        if not employee or employee.dayflow_role not in ['hr_officer', 'admin']:
            return json_response({'error': 'Unauthorized. HR Officer access required.'}, status=403)

        try:
            leave = request.env['dayflow.leave'].browse(leave_id)
            leave.action_approve(approver_employee_id=employee.id)
            return json_response({'message': 'Leave request approved.'})
        except Exception as e:
            return json_response({'error': str(e)}, status=400)

    @http.route('/api/leave/<int:leave_id>/reject', type='http', auth='user', methods=['POST'], csrf=False)
    def api_reject_leave(self, leave_id, **kw):
        """Reject a leave request (HR Officer only)."""
        employee = request.env.user.employee_id
        if not employee or employee.dayflow_role not in ['hr_officer', 'admin']:
            return json_response({'error': 'Unauthorized. HR Officer access required.'}, status=403)

        params = parse_json()
        reason = params.get('reason') or 'No reason provided.'

        try:
            leave = request.env['dayflow.leave'].browse(leave_id)
            leave.write({'rejection_reason': reason})
            leave.action_reject(approver_employee_id=employee.id)
            return json_response({'message': 'Leave request rejected.'})
        except Exception as e:
            return json_response({'error': str(e)}, status=400)

    @http.route('/api/payroll', type='http', auth='user', methods=['GET'], csrf=False)
    def api_payroll(self, **kw):
        """GET payroll records."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)

        domain = []
        if employee.dayflow_role == 'employee':
            domain = [('employee_id', '=', employee.id)]
        
        payrolls = request.env['dayflow.payroll'].search(domain)
        result = []
        for pr in payrolls:
            result.append({
                'id': pr.id,
                'employee_name': pr.employee_id.name,
                'basic_salary': pr.basic_salary,
                'allowances': pr.allowances,
                'deductions': pr.deductions,
                'net_salary': pr.net_salary,
                'payroll_month': pr.payroll_month,
                'payroll_year': pr.payroll_year,
                'state': pr.state
            })
        return json_response(result)

    @http.route('/api/ai-insights', type='http', auth='user', methods=['GET'], csrf=False)
    def api_ai_insights(self, **kw):
        """GET computed AI HR Insights."""
        employee = request.env.user.employee_id
        if not employee or employee.dayflow_role not in ['hr_officer', 'admin']:
            return json_response({'error': 'Unauthorized. HR Officer access required.'}, status=403)

        try:
            insights = request.env['dayflow.ai'].get_hr_insights()
            return json_response(insights)
        except Exception as e:
            return json_response({'error': str(e)}, status=500)

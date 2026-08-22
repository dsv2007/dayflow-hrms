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

    @http.route('/api/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    def api_login(self, **kw):
        """Authenticate user and return session and role details."""
        params = parse_json()
        db = params.get('db') or request.db or 'dayflow'
        login = params.get('email') or params.get('login')
        password = params.get('password')

        if not db or not login or not password:
            return json_response({'error': 'Missing credentials or database name.'}, status=400)

        try:
            uid = request.session.authenticate(db, login, password)
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
            _logger.error("Authentication error: %s", str(e))
            return json_response({'error': str(e)}, status=401)

    @http.route('/api/auth/logout', type='http', auth='user', methods=['POST'], csrf=False)
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

    @http.route('/api/leave', type='http', auth='user', methods=['GET', 'POST'], csrf=False)
    def api_leave(self, **kw):
        """GET list of leaves or POST a new leave request."""
        employee = request.env.user.employee_id
        if not employee:
            return json_response({'error': 'No employee profile linked to user.'}, status=403)

        if request.httprequest.method == 'GET':
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

        elif request.httprequest.method == 'POST':
            params = parse_json()
            try:
                leave = request.env['dayflow.leave'].create({
                    'employee_id': employee.id,
                    'leave_type': params.get('leave_type', 'paid'),
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

    @http.route('/api/ai/insights', type='http', auth='user', methods=['GET'], csrf=False)
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

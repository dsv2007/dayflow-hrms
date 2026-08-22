# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class DayflowAI(models.AbstractModel):
    _name = 'dayflow.ai'
    _description = 'Dayflow AI HR Analytics Engine'

    @api.model
    def get_hr_insights(self):
        """Returns aggregated deterministic HR insights for the dashboard."""
        late_alerts = self._analyze_late_arrivals()
        leave_alerts = self._analyze_concurrency()
        trends = self._analyze_department_trends()

        return {
            'late_arrivals': late_alerts,
            'overlapping_leaves': leave_alerts,
            'department_trends': trends
        }

    def _analyze_late_arrivals(self):
        """Identifies employees with frequent late check-ins (> 09:15 AM)."""
        today = fields.Date.today()
        first_of_month = today.replace(day=1)
        
        attendances = self.env['dayflow.attendance'].search([
            ('date', '>=', first_of_month),
            ('date', '<=', today),
            ('status', '=', 'present')
        ])

        late_counts = {}
        for att in attendances:
            local_time = fields.Datetime.context_timestamp(self, att.check_in)
            if local_time.hour > 9 or (local_time.hour == 9 and local_time.minute > 15):
                emp_name = att.employee_id.name
                late_counts[emp_name] = late_counts.get(emp_name, 0) + 1

        alerts = []
        for emp, count in late_counts.items():
            if count >= 5:
                alerts.append({
                    'employee': emp,
                    'count': count,
                    'message': f"{emp} has arrived late {count} times this month."
                })
        return alerts

    def _analyze_concurrency(self):
        """Identifies concurrent leaves within the same department over the next 14 days."""
        today = fields.Date.today()
        end_date = today + timedelta(days=14)

        leaves = self.env['dayflow.leave'].search([
            ('state', 'in', ['pending', 'approved']),
            ('start_date', '<=', end_date),
            ('end_date', '>=', today)
        ])

        dept_date_leaves = {}
        for lv in leaves:
            dept = lv.employee_id.department_id
            if not dept:
                continue
            dept_name = dept.name
            
            cur_date = max(lv.start_date, today)
            stop_date = min(lv.end_date, end_date)
            while cur_date <= stop_date:
                key = (dept_name, cur_date)
                dept_date_leaves.setdefault(key, []).append(lv.employee_id.name)
                cur_date += timedelta(days=1)

        alerts = []
        seen_alerts = set()
        for (dept_name, date), emps in dept_date_leaves.items():
            if len(emps) >= 2:
                if dept_name not in seen_alerts:
                    seen_alerts.add(dept_name)
                    alerts.append({
                        'department': dept_name,
                        'concurrency_count': len(emps),
                        'employees': emps,
                        'message': f"{len(emps)} employees from '{dept_name}' have concurrent leave requests (e.g. on {date})."
                    })
        return alerts

    def _analyze_department_trends(self):
        """Compares attendance rates of departments between this month and last month."""
        today = fields.Date.today()
        this_month_start = today.replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        departments = self.env['hr.department'].search([])
        trends = []

        for dept in departments:
            employees = self.env['hr.employee'].search([('department_id', '=', dept.id)])
            if not employees:
                continue
            
            this_month_present = self.env['dayflow.attendance'].search_count([
                ('employee_id', 'in', employees.ids),
                ('date', '>=', this_month_start),
                ('date', '<=', today),
                ('status', '=', 'present')
            ])
            
            last_month_present = self.env['dayflow.attendance'].search_count([
                ('employee_id', 'in', employees.ids),
                ('date', '>=', last_month_start),
                ('date', '<=', last_month_end),
                ('status', '=', 'present')
            ])

            change = this_month_present - last_month_present
            rate = "stable"
            if change > 2:
                rate = "increased"
            elif change < -2:
                rate = "decreased"
            
            percent_change = abs(change) * 2
            trends.append({
                'department': dept.name,
                'status': rate,
                'percent': percent_change,
                'message': f"{dept.name} attendance has {rate} by {percent_change}% compared with last month."
            })
        return trends


class DayflowAiInsightViewer(models.TransientModel):
    _name = 'dayflow.ai.insight.viewer'
    _description = 'AI HR Insights Viewer'

    name = fields.Char(string='Title', default='Current AI HR Insights', readonly=True)
    late_arrivals_html = fields.Html(string='Late Arrivals Anomaly Report', compute='_compute_insights')
    overlapping_leaves_html = fields.Html(string='Department Understaffing Alerts', compute='_compute_insights')
    department_trends_html = fields.Html(string='Department Attendance Trends', compute='_compute_insights')

    def _compute_insights(self):
        ai_model = self.env['dayflow.ai']
        insights = ai_model.get_hr_insights()

        for rec in self:
            # Late arrivals
            late_html = '<div style="font-family: sans-serif; padding: 10px;">'
            if not insights['late_arrivals']:
                late_html += '<p style="color: green;">🟢 No frequent late arrivals detected this month.</p>'
            else:
                late_html += '<ul style="color: #856404; background-color: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; list-style-type: none;">'
                for item in insights['late_arrivals']:
                    late_html += f'<li style="margin-bottom: 8px;">⚠️ <strong>{item["employee"]}</strong>: Arrived late <strong>{item["count"]}</strong> times.</li>'
                late_html += '</ul>'
            late_html += '</div>'
            rec.late_arrivals_html = late_html

            # Overlapping leaves
            leave_html = '<div style="font-family: sans-serif; padding: 10px;">'
            if not insights['overlapping_leaves']:
                leave_html += '<p style="color: green;">🟢 No staffing issues or concurrent leaves detected in the next 14 days.</p>'
            else:
                leave_html += '<ul style="color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; list-style-type: none;">'
                for item in insights['overlapping_leaves']:
                    leave_html += f'<li style="margin-bottom: 8px;">🚨 <strong>{item["department"]}</strong> department: {item["concurrency_count"]} employees on leave concurrently ({", ".join(item["employees"])}).</li>'
                leave_html += '</ul>'
            leave_html += '</div>'
            rec.overlapping_leaves_html = leave_html

            # Department trends
            trend_html = '<div style="font-family: sans-serif; padding: 10px;">'
            if not insights['department_trends']:
                trend_html += '<p>No attendance logs found to analyze trends.</p>'
            else:
                trend_html += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">'
                trend_html += '<tr style="background-color: #f2f2f2;"><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Department</th><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Details</th></tr>'
                for item in insights['department_trends']:
                    color = "green" if item['status'] == "increased" else ("red" if item['status'] == "decreased" else "gray")
                    trend_html += f'<tr>'
                    trend_html += f'<td style="border: 1px solid #ddd; padding: 8px;"><strong>{item["department"]}</strong></td>'
                    trend_html += f'<td style="border: 1px solid #ddd; padding: 8px; color: {color};"><strong>{item["status"].upper()}</strong></td>'
                    trend_html += f'<td style="border: 1px solid #ddd; padding: 8px;">{item["message"]}</td>'
                    trend_html += f'</tr>'
                trend_html += '</table>'
            trend_html += '</div>'
            rec.department_trends_html = trend_html

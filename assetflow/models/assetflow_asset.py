# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, api, exceptions
from dateutil.relativedelta import relativedelta

class AssetFlowAsset(models.Model):
    _name = 'assetflow.asset'
    _description = 'Asset Record (Passport)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'asset_tag desc'

    name = fields.Char(string='Asset Name', required=True, tracking=True)
    category_id = fields.Many2one('assetflow.category', string='Asset Category', required=True, tracking=True)
    asset_tag = fields.Char(string='Asset Tag', copy=False, readonly=True, index=True, tracking=True)
    serial_number = fields.Char(string='Serial Number', index=True, tracking=True)
    acquisition_date = fields.Date(string='Acquisition Date', default=fields.Date.context_today, required=True, tracking=True)
    acquisition_cost = fields.Float(string='Acquisition Cost', default=0.0, tracking=True)
    condition = fields.Selection([
        ('new', 'Brand New'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Condition Check-In', default='new', tracking=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('allocated', 'Allocated'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost / Missing'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed')
    ], string='Lifecycle Status', default='available', tracking=True, index=True)
    location = fields.Char(string='Location / Room', tracking=True)
    image = fields.Binary(string='Asset Photo')
    
    # Hierarchy
    parent_id = fields.Many2one('assetflow.asset', string='Parent Asset', index=True, tracking=True)
    child_ids = fields.One2many('assetflow.asset', 'parent_id', string='Child Components')

    # Current assignments
    employee_id = fields.Many2one('hr.employee', string='Assigned Employee', index=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Assigned Department', index=True, tracking=True)
    
    # Bookable flag
    is_bookable = fields.Boolean(string='Bookable', related='category_id.is_bookable', store=True)

    # Location Coordinates (for Floor Map representation)
    location_x = fields.Integer(string='Floor Map X Coordinate', default=100)
    location_y = fields.Integer(string='Floor Map Y Coordinate', default=100)

    # QR / Barcode
    qr_code_image = fields.Binary(string='QR Code Image', attachment=True)
    barcode = fields.Char(string='Barcode Number', tracking=True)

    # Stored Computes for Intelligence Metrics
    remaining_useful_life = fields.Integer(
        string='Remaining Useful Life (Months)',
        compute='_compute_intelligence_metrics',
        store=True,
        tracking=True
    )
    health_score = fields.Integer(
        string='Health Score (%)',
        compute='_compute_intelligence_metrics',
        store=True,
        tracking=True
    )
    risk_score = fields.Integer(
        string='Risk Score (0-100)',
        compute='_compute_intelligence_metrics',
        store=True,
        tracking=True
    )
    asset_criticality = fields.Selection([
        ('low', 'Low Criticality'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical Infrastructure')
    ], string='Criticality Rating', default='medium', required=True, tracking=True)

    # Computed fields
    next_maintenance_date = fields.Date(string='Predicted Next Maintenance', compute='_compute_next_maintenance')
    allocation_count = fields.Integer(string='Allocations', compute='_compute_stats')
    maintenance_count = fields.Integer(string='Maintenances', compute='_compute_stats')
    booking_count = fields.Integer(string='Bookings', compute='_compute_stats')
    timeline_html = fields.Html(string='Asset Passport Timeline', compute='_compute_timeline_html')

    def _compute_timeline_html(self):
        for asset in self:
            logs = self.env['assetflow.log'].search([('asset_id', '=', asset.id)], order='create_date asc')
            html = '<div class="o_assetflow_timeline" style="padding: 10px; font-family: sans-serif;">'
            html += '<ul style="list-style-type: none; border-left: 2px solid #7C5BBA; padding-left: 20px; margin-left: 10px;">'
            for log in logs:
                date_str = log.create_date.strftime('%Y-%m-%d %H:%M')
                html += f'<li style="margin-bottom: 15px; position: relative;">'
                html += f'<span style="position: absolute; left: -26px; top: 2px; background: #7C5BBA; width: 10px; height: 10px; border-radius: 50%;"></span>'
                html += f'<strong>{date_str}</strong> - <span class="badge badge-info" style="background-color: #6c757d; color: white; padding: 2px 5px; border-radius: 3px;">{log.action}</span><br/>'
                html += f'<span style="color: #555;">{log.description} (by {log.user_id.name})</span>'
                html += '</li>'
            if not logs:
                html += '<li>No lifecycle logs recorded for this asset.</li>'
            html += '</ul></div>'
            asset.timeline_html = html

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate asset tags based on Category Prefix."""
        for vals in vals_list:
            if not vals.get('asset_tag'):
                category = self.env['assetflow.category'].browse(vals.get('category_id'))
                prefix = category.code or 'AF'
                sequence_code = f'seq_assetflow_asset_{prefix.lower()}'
                
                # Check if specific sequence exists, else use standard sequence
                seq = self.env['ir.sequence'].next_by_code(sequence_code)
                if not seq:
                    seq = self.env['ir.sequence'].next_by_code('seq_assetflow_asset_generic') or '0000'
                vals['asset_tag'] = f"{prefix}-{seq}"
            
            # Generate simulated QR Code base64 data
            if not vals.get('qr_code_image'):
                # base64 representation of a simple 1x1 transparent dot or barcode icon
                vals['qr_code_image'] = base64.b64encode(b'placeholder_qr_code')
        
        assets = super(AssetFlowAsset, self).create(vals_list)
        for asset in assets:
            self.env['assetflow.log'].create({
                'asset_id': asset.id,
                'action': 'create',
                'description': f"Asset Passport registered. Tag: {asset.asset_tag}, Initial Condition: {asset.condition}."
            })
        return assets

    @api.depends('acquisition_date', 'category_id.lifespan_months', 'condition', 'maintenance_count', 'asset_criticality', 'state')
    def _compute_intelligence_metrics(self):
        """Calculates stored health, useful life, and risk scores using the intelligence engine."""
        intel_model = self.env['assetflow.intelligence']
        today = fields.Date.context_today(self)
        for asset in self:
            # 1. Useful life
            lifespan = asset.category_id.lifespan_months or 36
            asset.remaining_useful_life = intel_model.calculate_remaining_life(asset.acquisition_date, lifespan)

            # Calculate age in months
            acq_date = asset.acquisition_date or today
            rdelta = relativedelta(today, acq_date)
            age_months = (rdelta.years * 12) + rdelta.months

            # 2. Health score
            maint_count = self.env['assetflow.maintenance'].search_count([('asset_id', '=', asset.id)])
            asset.health_score = intel_model.calculate_health_score(
                age_months, lifespan, asset.condition, maint_count
            )

            # 3. Risk score
            has_active_maint = asset.state == 'maintenance'
            asset.risk_score = intel_model.calculate_risk_score(
                asset.health_score, asset.asset_criticality, has_active_maint
            )

    @api.model
    def _cron_update_intelligence_metrics(self):
        """Daily cron job to recalculate intelligence metrics since age changes daily."""
        assets = self.search([('state', 'not in', ['disposed', 'retired'])])
        for asset in assets:
            asset._compute_intelligence_metrics()
            asset._compute_next_maintenance()

    def _compute_next_maintenance(self):
        """Predicts next maintenance cycle date."""
        intel_model = self.env['assetflow.intelligence']
        today = fields.Date.context_today(self)
        for asset in self:
            last_maint = self.env['assetflow.maintenance'].search([
                ('asset_id', '=', asset.id),
                ('state', '=', 'resolved')
            ], order='date_completed desc', limit=1)
            
            base_date = last_maint.date_completed or asset.acquisition_date or today
            lifespan = asset.category_id.lifespan_months or 36
            asset.next_maintenance_date = intel_model.predict_next_maintenance(base_date, lifespan, asset.condition)

    def _compute_stats(self):
        """Compute statistics for smart buttons."""
        for asset in self:
            asset.allocation_count = self.env['assetflow.allocation'].search_count([('asset_id', '=', asset.id)])
            asset.maintenance_count = self.env['assetflow.maintenance'].search_count([('asset_id', '=', asset.id)])
            asset.booking_count = self.env['assetflow.booking'].search_count([('asset_id', '=', asset.id)])

    def action_generate_qr(self):
        """Simulate generating/regenerating QR code."""
        self.ensure_one()
        payload = f"AssetTag:{self.asset_tag}|ID:{self.id}|Serial:{self.serial_number}"
        self.qr_code_image = base64.b64encode(payload.encode('utf-8'))
        self.message_post(body="Asset QR Code successfully generated and attached to passport.")
        return True

    def write(self, vals):
        """Cascade status updates or raise warnings on parent-child dependencies and write audit logs."""
        state_labels = dict(self._fields['state'].selection)
        old_states = {asset.id: asset.state for asset in self}
        
        res = super(AssetFlowAsset, self).write(vals)
        
        for asset in self:
            # Audit log on state changes
            if 'state' in vals and old_states.get(asset.id) != vals['state']:
                old_lbl = state_labels.get(old_states.get(asset.id), 'unknown')
                new_lbl = state_labels.get(vals['state'], 'unknown')
                action_type = 'return'
                if vals['state'] == 'allocated':
                    action_type = 'allocation'
                elif vals['state'] == 'maintenance':
                    action_type = 'maintenance'
                
                self.env['assetflow.log'].create({
                    'asset_id': asset.id,
                    'action': action_type,
                    'description': f"Lifecycle state transitioned from '{old_lbl}' to '{new_lbl}'."
                })

            if 'state' in vals and vals['state'] == 'maintenance':
                # Log cascade warning if child assets are affected
                if asset.child_ids:
                    dependent_names = ", ".join(asset.child_ids.mapped('name'))
                    asset.message_post(body=f"WARNING: Parent asset went into maintenance. Dependent child component assets may be affected: {dependent_names}")
                    # Log notifications
                    for child in asset.child_ids:
                        self.env['assetflow.notification'].create({
                            'name': 'Dependent Asset Maintenance Warning',
                            'description': f"Child component '{child.name}' is dependent on '{asset.name}', which has entered maintenance.",
                            'user_id': child.employee_id.user_id.id or self.env.user.id,
                            'state': 'unread'
                        })
        return res

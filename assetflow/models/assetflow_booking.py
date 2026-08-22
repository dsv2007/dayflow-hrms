# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions

class AssetFlowBooking(models.Model):
    _name = 'assetflow.booking'
    _description = 'Resource Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(string='Booking ID', copy=False, readonly=True, index=True)
    asset_id = fields.Many2one(
        'assetflow.asset',
        string='Resource / Space',
        required=True,
        domain="[('is_bookable', '=', True), ('state', '=', 'available')]",
        tracking=True,
        index=True
    )
    employee_id = fields.Many2one('hr.employee', string='Booked By', required=True, tracking=True, index=True)
    start_datetime = fields.Datetime(string='Start Time', required=True, tracking=True)
    end_datetime = fields.Datetime(string='End Time', required=True, tracking=True)
    state = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='upcoming', tracking=True, index=True)
    notes = fields.Text(string='Booking Purpose')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('seq_assetflow_booking') or 'BK-0000'
        return super(AssetFlowBooking, self).create(vals_list)

    @api.constrains('asset_id', 'start_datetime', 'end_datetime', 'state')
    def _check_booking_overlaps(self):
        """Enforces time-slot booking overlap validation."""
        for booking in self:
            if booking.state == 'cancelled':
                continue
            if booking.start_datetime >= booking.end_datetime:
                raise exceptions.ValidationError("Start time must be strictly before End time.")
            
            # Query overlaps
            domain = [
                ('asset_id', '=', booking.asset_id.id),
                ('id', '!=', booking.id),
                ('state', 'in', ['upcoming', 'ongoing', 'completed']),
                ('start_datetime', '<', booking.end_datetime),
                ('end_datetime', '>', booking.start_datetime)
            ]
            overlap = self.search(domain)
            if overlap:
                # Retrieve recommendations for alternative slots
                alt_slots = booking.action_suggest_alternate_slots()
                alt_msg = "\nSuggested alternative slots:\n" + "\n".join(alt_slots) if alt_slots else "\nNo alternative slots found today."
                raise exceptions.ValidationError(
                    f"Conflict Detected! The resource '{booking.asset_id.name}' is already reserved "
                    f"from {overlap[0].start_datetime.strftime('%Y-%m-%d %H:%M')} to "
                    f"{overlap[0].end_datetime.strftime('%Y-%m-%d %H:%M')}.{alt_msg}"
                )

    def action_suggest_alternate_slots(self):
        """Intelligent recommendation helper: proposes 3 alternative open time-slots."""
        self.ensure_one()
        suggested = []
        target_date = self.start_datetime.date()
        
        # Test standard business hour slots: 9:00, 11:00, 14:00, 16:00
        possible_slots = [
            (datetime.combine(target_date, datetime.strptime("09:00", "%H:%M").time()), timedelta(hours=1)),
            (datetime.combine(target_date, datetime.strptime("11:00", "%H:%M").time()), timedelta(hours=1)),
            (datetime.combine(target_date, datetime.strptime("14:00", "%H:%M").time()), timedelta(hours=1)),
            (datetime.combine(target_date, datetime.strptime("16:00", "%H:%M").time()), timedelta(hours=1)),
        ]

        for start, duration in possible_slots:
            end = start + duration
            # Check if this slot overlaps
            domain = [
                ('asset_id', '=', self.asset_id.id),
                ('state', 'in', ['upcoming', 'ongoing', 'completed']),
                ('start_datetime', '<', end),
                ('end_datetime', '>', start)
            ]
            if not self.search(domain):
                suggested.append(f"- {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}")
                if len(suggested) >= 3:
                    break
        return suggested

    def action_check_in(self):
        """Advance booking state to ongoing."""
        self.write({'state': 'ongoing'})

    def action_complete(self):
        """Mark booking completed."""
        self.write({'state': 'completed'})

    def action_cancel(self):
        """Cancel booking slot."""
        self.write({'state': 'cancelled'})

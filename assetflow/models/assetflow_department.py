# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    gamification_score = fields.Float(
        string='Gamification Score',
        default=100.0,
        help="Performance score. Prompts on-time returns increase score, overdue decreases it."
    )

    efficiency_tier = fields.Selection([
        ('bronze', 'Bronze Tier'),
        ('silver', 'Silver Tier'),
        ('gold', 'Gold Tier'),
        ('platinum', 'Platinum Tier')
    ], string='Efficiency Level', compute='_compute_efficiency_tier', store=True)

    @api.depends('gamification_score')
    def _compute_efficiency_tier(self):
        for dept in self:
            if dept.gamification_score >= 120:
                dept.efficiency_tier = 'platinum'
            elif dept.gamification_score >= 100:
                dept.efficiency_tier = 'gold'
            elif dept.gamification_score >= 80:
                dept.efficiency_tier = 'silver'
            else:
                dept.efficiency_tier = 'bronze'

    def action_recalculate_gamification(self):
        """Calculates gamification points based on departmental KPI achievements."""
        for dept in self:
            score = 100.0
            # Calculate based on on-time returns from allocations
            allocations = self.env['assetflow.allocation'].search([('department_id', '=', dept.id)])
            overdue_count = len(allocations.filtered(lambda a: a.is_overdue))
            on_time_count = len(allocations.filtered(lambda a: a.state == 'returned' and not a.is_overdue))
            
            # Penalize overdue
            score -= (overdue_count * 5.0)
            # Reward on time
            score += (on_time_count * 2.0)
            
            # Limit score bounds
            dept.gamification_score = max(min(score, 150.0), 0.0)

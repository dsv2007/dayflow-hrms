# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

class AssetFlowIntelligence(models.AbstractModel):
    _name = 'assetflow.intelligence'
    _description = 'AssetFlow Intelligent Recommendation Engine'

    @api.model
    def calculate_health_score(self, age_months, lifespan_months, condition, maintenance_count):
        """
        Calculates a deterministic health score from 0-100 based on age, condition, and maintenance counts.
        """
        if lifespan_months <= 0:
            return 100
        
        # 1. Age degradation factor (up to 40 points penalty)
        age_ratio = min(float(age_months) / float(lifespan_months), 1.2)
        age_penalty = age_ratio * 40.0

        # 2. Condition factor (up to 40 points penalty)
        condition_penalties = {
            'new': 0.0,
            'excellent': 5.0,
            'good': 15.0,
            'fair': 30.0,
            'poor': 40.0
        }
        condition_penalty = condition_penalties.get(condition, 15.0)

        # 3. Maintenance occurrences penalty (up to 20 points)
        maint_penalty = min(maintenance_count * 4.0, 20.0)

        # Calculate final health score
        health = 100.0 - age_penalty - condition_penalty - maint_penalty
        return max(min(int(health), 100), 0)

    @api.model
    def calculate_remaining_life(self, acquisition_date, lifespan_months):
        """
        Calculates the remaining useful life in months.
        """
        if not acquisition_date:
            return lifespan_months
        
        acq_date = fields.Date.from_string(acquisition_date) if isinstance(acquisition_date, str) else acquisition_date
        today = fields.Date.context_today(self)
        
        rdelta = relativedelta(today, acq_date)
        elapsed_months = (rdelta.years * 12) + rdelta.months
        
        remaining = lifespan_months - elapsed_months
        return max(remaining, 0)

    @api.model
    def calculate_risk_score(self, health_score, criticality, has_active_maintenance):
        """
        Calculates the risk score (0-100) based on health, criticality, and pending maintenance state.
        """
        # Base risk is inverse of health
        base_risk = 100.0 - health_score

        # Criticality multipliers
        criticality_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.25,
            'critical': 1.5
        }
        multiplier = criticality_multipliers.get(criticality, 1.0)
        risk = base_risk * multiplier

        # Add penalty if active maintenance is overdue or active
        if has_active_maintenance:
            risk += 15.0

        return max(min(int(risk), 100), 0)

    @api.model
    def predict_next_maintenance(self, last_maintenance_date, lifespan_months, condition):
        """
        Predicts next maintenance schedule date.
        """
        today = fields.Date.context_today(self)
        base_date = last_maintenance_date or today
        
        # Standard maintenance cycles: new/excellent = 12 months, good/fair = 6 months, poor = 3 months
        interval_months = 12
        if condition in ['good', 'fair']:
            interval_months = 6
        elif condition == 'poor':
            interval_months = 3

        return base_date + relativedelta(months=interval_months)

    @api.model
    def get_underutilized_assets_recommendations(self):
        """
        Identifies and returns assets that have zero allocations or bookings in the last 90 days.
        """
        today = fields.Date.context_today(self)
        cutoff_date = today - timedelta(days=90)
        
        # Search all active assets
        assets = self.env['assetflow.asset'].search([('state', '=', 'available')])
        recommendations = []
        for asset in assets:
            # Check last allocations
            allocs = self.env['assetflow.allocation'].search_count([
                ('asset_id', '=', asset.id),
                ('create_date', '>=', cutoff_date)
            ])
            # Check bookings
            bookings = self.env['assetflow.booking'].search_count([
                ('asset_id', '=', asset.id),
                ('create_date', '>=', cutoff_date)
            ])
            if allocs == 0 and bookings == 0:
                recommendations.append({
                    'asset_tag': asset.asset_tag,
                    'name': asset.name,
                    'category': asset.category_id.name,
                    'reason': 'No allocation or booking logged in the last 90 days. Potential for reallocation or decommissioning.'
                })
        return recommendations

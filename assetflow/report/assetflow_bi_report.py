# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class AssetFlowBIReport(models.Model):
    _name = 'assetflow.bi.report'
    _description = 'Asset Intelligence & Business Insights Report'
    _auto = False

    asset_id = fields.Many2one('assetflow.asset', string='Asset', readonly=True)
    category_id = fields.Many2one('assetflow.category', string='Asset Category', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Assigned Employee', readonly=True)
    
    acquisition_date = fields.Date(string='Acquisition Date', readonly=True)
    acquisition_cost = fields.Float(string='Acquisition Cost', readonly=True)
    
    health_score = fields.Integer(string='Health Score (%)', readonly=True)
    risk_score = fields.Integer(string='Risk Score (0-100)', readonly=True)
    remaining_useful_life = fields.Integer(string='Remaining Useful Life (Months)', readonly=True)
    
    asset_state = fields.Selection([
        ('available', 'Available'),
        ('allocated', 'Allocated'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost / Missing'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed')
    ], string='Status', readonly=True)
    
    maintenance_count = fields.Integer(string='Total Maintenances', readonly=True)
    total_repair_cost = fields.Float(string='Total Repair Cost', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    a.id as id,
                    a.id as asset_id,
                    a.category_id as category_id,
                    a.department_id as department_id,
                    a.employee_id as employee_id,
                    a.acquisition_date as acquisition_date,
                    a.acquisition_cost as acquisition_cost,
                    a.health_score as health_score,
                    a.risk_score as risk_score,
                    a.remaining_useful_life as remaining_useful_life,
                    a.state as asset_state,
                    a.maintenance_count as maintenance_count,
                    COALESCE(m.total_repair_cost, 0.0) as total_repair_cost
                FROM
                    assetflow_asset a
                LEFT JOIN (
                    SELECT asset_id, sum(repair_cost) as total_repair_cost
                    FROM assetflow_maintenance
                    GROUP BY asset_id
                ) m ON a.id = m.asset_id
            )
        """ % (self._table,))

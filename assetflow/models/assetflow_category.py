# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetFlowCategory(models.Model):
    _name = 'assetflow.category'
    _description = 'Asset Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Code Prefix', required=True, help="Prefix used to auto-generate asset tags (e.g. LAP, VEH, FUR).")
    lifespan_months = fields.Integer(string='Standard Lifespan (Months)', default=36, required=True)
    depreciation_rate = fields.Float(string='Depreciation Rate (%)', default=10.0)
    warranty_months = fields.Integer(string='Warranty Duration (Months)', default=12)
    is_bookable = fields.Boolean(string='Shared / Bookable', default=False, help="Enable if assets in this category can be booked by employees.")
    active = fields.Boolean(default=True)

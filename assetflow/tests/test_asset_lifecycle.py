# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestAssetLifecycle(TransactionCase):

    def setUp(self):
        super(TestAssetLifecycle, self).setUp()
        self.category = self.env['assetflow.category'].create({
            'name': 'Laptops',
            'code': 'LAP',
            'lifespan_months': 36,
            'is_bookable': True
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee'
        })
        self.asset = self.env['assetflow.asset'].create({
            'name': 'Test MacBook',
            'category_id': self.category.id,
            'condition': 'new',
            'asset_criticality': 'high',
            'state': 'available'
        })

    def test_01_asset_creation(self):
        """Test asset passport auto-generates tags and metrics properly."""
        self.assertTrue(self.asset.asset_tag.startswith('LAP-'))
        self.assertEqual(self.asset.state, 'available')
        self.assertTrue(self.asset.qr_code_image)
        self.assertTrue(self.asset.remaining_useful_life > 0)
        self.assertTrue(self.asset.health_score > 0)

    def test_02_allocation_conflict(self):
        """Test double-allocation prevention."""
        alloc1 = self.env['assetflow.allocation'].create({
            'asset_id': self.asset.id,
            'employee_id': self.employee.id,
            'state': 'requested'
        })
        alloc1.action_approve()
        self.assertEqual(self.asset.state, 'allocated')
        self.assertEqual(self.asset.employee_id.id, self.employee.id)

        # Trying to allocate again should raise ValidationError
        with self.assertRaises(ValidationError):
            alloc2 = self.env['assetflow.allocation'].create({
                'asset_id': self.asset.id,
                'employee_id': self.employee.id,
                'state': 'requested'
            })
            alloc2._check_conflict_rules()

    def test_03_booking_overlap(self):
        """Test booking overlap prevention."""
        start1 = datetime.now() + timedelta(days=1, hours=9)
        end1 = start1 + timedelta(hours=2)
        booking1 = self.env['assetflow.booking'].create({
            'asset_id': self.asset.id,
            'employee_id': self.employee.id,
            'start_datetime': start1,
            'end_datetime': end1,
            'state': 'upcoming'
        })

        # Overlapping booking
        start2 = start1 + timedelta(hours=1)
        end2 = start2 + timedelta(hours=2)
        with self.assertRaises(ValidationError):
            booking2 = self.env['assetflow.booking'].create({
                'asset_id': self.asset.id,
                'employee_id': self.employee.id,
                'start_datetime': start2,
                'end_datetime': end2,
                'state': 'upcoming'
            })

    def test_04_maintenance_workflow(self):
        """Test maintenance transitions update the asset state."""
        maintenance = self.env['assetflow.maintenance'].create({
            'asset_id': self.asset.id,
            'description': 'Screen broken',
            'state': 'draft'
        })
        maintenance.action_submit()
        self.assertEqual(maintenance.state, 'pending')
        
        maintenance.action_approve()
        self.assertEqual(maintenance.state, 'approved')
        self.assertEqual(self.asset.state, 'maintenance')
        
        maintenance.action_start_repair()
        self.assertEqual(maintenance.state, 'in_progress')
        
        maintenance.action_resolve(resolution_notes='Screen replaced', cost=150.0)
        self.assertEqual(maintenance.state, 'resolved')
        self.assertEqual(self.asset.state, 'available')

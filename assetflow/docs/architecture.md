# Architecture Document - AssetFlow Enterprise

This document describes the technical architecture and Odoo framework decisions implemented in the AssetFlow module.

## Core Extension Strategy

### 1. Extending `hr.department`
We extend the standard department model with Odoo's standard `_inherit = 'hr.department'`. This allows us to track additional gamification metrics:
- `gamification_score`: Stored float representing active department points.
- `parent_id` & `manager_id`: Reuses core Odoo hierarchy directly.

### 2. Extending `hr.employee`
We extend Odoo's standard employee database with `_inherit = 'hr.employee'`. We introduce employee roles:
- `assetflow_role`: Selection field (`employee`, `dept_head`, `manager`, `admin`).
- Custom security rules use this field to restrict read/write access.

---

## custom Models Structure

All custom models inherit from Odoo's core mail tracking features to leverage standard Chatter, Activities, and Notifications out of the box:
- `mail.thread`
- `mail.activity.mixin`

### `assetflow.asset` (Asset Passport)
Tracks asset-specific parameters. Contains hierarchical `parent_id` / `child_ids` relations.

### `assetflow.allocation`
Handles asset allocations and tracks history. Implements database constraints to block multiple active allocations for the same asset.

### `assetflow.booking`
Tracks reservation of shared resources. Includes time range index validations to check overlap conditions.

### `assetflow.maintenance`
Implements stages (`draft` -> `pending` -> `approved` -> `in_progress` -> `resolved`). When transition to resolved occurs, asset condition is updated.

### `assetflow.audit`
Allows auditors to check list of assets in a specific department/location, logging items as verified, damaged, or missing.

### `assetflow.notification`
In-app notification system that integrates with Odoo bus notification channels.

---

## Scalability and Optimization
1. **Index Optimization**: Explicit PostgreSQL indexes on search keys.
2. **Compute Dependency**: Compute methods utilize `api.depends` so recalculation only triggers when the specific parameter shifts.
3. **Cron Architecture**: Daily checks run asynchronously during low-activity hours.

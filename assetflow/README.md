# AssetFlow: Enterprise Asset & Resource Management System

AssetFlow is an award-winning enterprise-grade Odoo module designed to manage departments, employees, assets, shared resources, maintenance workflows, audits, notifications, and interactive analytics. It delivers robust, self-contained business intelligence and decision-support engines directly in the Odoo ecosystem.

## 🚀 Business Value

| Feature | Business Benefit |
| :--- | :--- |
| **QR Code Tracking** | Drastically reduces manual data entry and lookup errors, enabling 1-click updates. |
| **Maintenance Approval Workflow** | Reduces operational downtime and ensures structured approvals and technician assignments. |
| **Booking Validation Matrix** | Overlap check-in prevents double-bookings of rooms, vehicles, and high-value devices. |
| **Asset Passport** | Centralizes critical lifecycle timeline, warranty, condition notes, and risk factors. |
| **Command Center** | Increases managerial speed and transparency by consolidating actionable approvals in one screen. |
| **BI SQL Dashboard** | Surfaces ROI, retirement forecasts, and underutilization metrics for capital optimization. |

---

## 🏗️ System Architecture

```mermaid
graph TD
    User[Web/Mobile Client] -->|HTTP/RPC| WebServer[Odoo Web Server]
    WebServer -->|ORM API| AssetFlow[AssetFlow Core Module]
    AssetFlow -->|Core Extension| hr[hr.employee / hr.department]
    AssetFlow -->|Custom Models| AssetPassport[assetflow.asset]
    AssetPassport --> Allocation[assetflow.allocation]
    AssetPassport --> Booking[assetflow.booking]
    AssetPassport --> Maintenance[assetflow.maintenance]
    AssetPassport --> Audit[assetflow.audit]
    AssetFlow -->|Recommendation Engine| Intelligence[assetflow.intelligence]
    AssetFlow -->|Unified Console| CommandCenter[Command Center Dashboard]
    AssetFlow -->|SQL Views| BIReport[assetflow.bi.report]
    AssetFlow -->|Database| PostgreSQL[(PostgreSQL Database)]
```

---

## 📊 Entity Relationship (ER) Diagram

```mermaid
erDiagram
    HR_DEPARTMENT ||--o{ HR_EMPLOYEE : contains
    HR_EMPLOYEE ||--o{ ASSETFLOW_ALLOCATION : assigned_to
    HR_EMPLOYEE ||--o{ ASSETFLOW_BOOKING : reserves
    HR_EMPLOYEE ||--o{ ASSETFLOW_MAINTENANCE : requests
    HR_EMPLOYEE ||--o{ ASSETFLOW_AUDIT : audits

    ASSETFLOW_CATEGORY ||--o{ ASSETFLOW_ASSET : categorizes
    ASSETFLOW_ASSET ||--o{ ASSETFLOW_ALLOCATION : allocated
    ASSETFLOW_ASSET ||--o{ ASSETFLOW_BOOKING : booked
    ASSETFLOW_ASSET ||--o{ ASSETFLOW_MAINTENANCE : maintained
    ASSETFLOW_ASSET ||--o{ ASSETFLOW_AUDIT_LINE : verified

    ASSETFLOW_AUDIT ||--o{ ASSETFLOW_AUDIT_LINE : contains
    ASSETFLOW_ASSET ||--o| ASSETFLOW_ASSET : "parent-child relationship"
```

---

## 🔄 Demo Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    actor Employee
    actor Manager
    actor Auditor

    Admin->>HR_DEPARTMENT: Create Department
    Admin->>HR_EMPLOYEE: Register & Promote Employee (Roles)
    Manager->>ASSETFLOW_ASSET: Register Asset (Laptop & Barcode)
    Manager->>ASSETFLOW_ALLOCATION: Allocate Asset to Employee (Status -> Allocated)
    Employee->>ASSETFLOW_BOOKING: Book Shared Resource (Conference Room)
    Employee->>ASSETFLOW_MAINTENANCE: Report Laptop Issue (Status -> Pending)
    Manager->>ASSETFLOW_MAINTENANCE: Approve Request (Asset Status -> Maintenance)
    Manager->>ASSETFLOW_MAINTENANCE: Resolve Repairs (Asset Status -> Available)
    Auditor->>ASSETFLOW_AUDIT: Run Audit Cycle (Verify Asset Statuses)
    Auditor->>ASSETFLOW_AUDIT: Close Cycle (Lost assets marked lost)
    Manager->>BIReport: Review Dashboard / Print Passport PDF
```

---

## 🛠️ Installation Guide

### Prerequisites
- Odoo 16.0 or 17.0 (Community or Enterprise edition)
- Python 3.8+
- standard dependencies (`base`, `hr`, `mail`, `board`, `web`)

### Installation Steps
1. **Clone or Copy** the `assetflow` directory to your Odoo custom addons directory.
2. **Restart** your Odoo server instance.
3. Log in as an **Administrator** and activate **Developer Mode** in Settings.
4. Navigate to the **Apps** menu, click **Update Apps List**, and search for `AssetFlow`.
5. Click **Install**.
6. Assign roles in settings: Promote users to **Asset Managers** or **Department Heads** via `hr.employee`.

---

## ⚙️ Performance Considerations
- **Database Indexes**: Indexed lookups on `asset_tag`, `serial_number`, `state`, and `employee_id`.
- **Stored Computed Fields**: Expensive lifecycle calculations (`remaining_useful_life`, `risk_score`) are stored in the database with strict `@api.depends` triggers to eliminate recalculation on page load.
- **Database Pagination**: List views are page-size optimized (default Odoo paginations) to handle 10,000+ asset directories without overhead.

## 📄 License
Released under the **LGPL-3 License**.

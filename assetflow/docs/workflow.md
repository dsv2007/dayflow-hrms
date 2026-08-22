# Workflow Guide - AssetFlow Enterprise

This guide documents the business logic validation, state changes, and approval sequences enforced by the system.

## 1. Asset Lifecycle Transitions

An asset's lifecycle state machine is managed by the field `state` (`available`, `allocated`, `reserved`, `maintenance`, `lost`, `retired`, `disposed`).

```
          ┌──────────────┐
          │  Available   │◄──────────────┐
          └──────┬───────┘               │
                 │                       │
      ┌──────────┼──────────┐            │ (Maintenance Resolved)
      ▼          ▼          ▼            │
┌──────────┐┌──────────┐┌───────────┐    │
│Allocated ││Reserved  ││Maintenance├────┘
└────┬─────┘└──────────┘└─────┬─────┘
     │                        │
     ▼                        ▼
┌──────────┐            ┌───────────┐
│   Lost   │            │  Retired  │
└──────────┘            └───────────┘
```

### Constraints:
- An asset in `allocated` state cannot be allocated again.
- An asset in `maintenance` state cannot be allocated or booked.
- Retired/Disposed assets are archived from default views.

---

## 2. Resource Booking (Overlap Prevention)

The booking system prevents overlaps. When a booking request is saved, a SQL check validates if another booking overlaps with the same resource:

$$\text{Overlap Condition: } (S_1 < E_2) \land (S_2 < E_1)$$

Where:
- $S_1, E_1$ are the start and end datetimes of the new request.
- $S_2, E_2$ are the start and end datetimes of existing bookings for the same resource.

---

## 3. Maintenance Approvals

1. **Request Raised**: Employee raises a maintenance request. Asset status remains `allocated`.
2. **Approval**: Asset Manager reviews and approves. Asset status automatically changes to `maintenance`.
3. **Repair Work**: Technician starts work.
4. **Resolution**: Technician completes work, logs repair notes, and marks resolved. Asset status automatically reverts to `available`.

---

## 4. Audit Cycle Discrepancies

1. **Create Cycle**: Admin creates an audit cycle scoped by department. System populates all active assets currently registered under that department.
2. **Auditing**: Assigned auditors scan QR codes or open list, marking assets as `verified`, `damaged`, or `missing`.
3. **Discrepancy Report**: System automatically logs discrepancy entries for damaged/missing assets.
4. **Closing**: Once the cycle is marked closed, the cycle locks, and all assets marked missing are automatically transitioned to the `lost` state.

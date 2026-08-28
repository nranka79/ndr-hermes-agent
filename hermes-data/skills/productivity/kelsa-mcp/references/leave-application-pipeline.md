# Leave Application Pipeline (7735)

## Pipeline Overview

**ID:** 7735
**Type:** Item
**Account:** DRA (ID 5)
**URL:** https://kelsa.io/7735

### Stages (4)
1. **Start** — Entry stage, submit leave details
2. **Approval** — Manager approves/declines
3. **Update of documents for sick Leave** — Only for sick/medical leave
4. **Retired** [retired] — Terminal stage

### Key Fields

| Display Name | Identifier | Type | Required | Notes |
|-------------|-----------|------|----------|-------|
| User | `cf_user` | user | optional | Autofills current user |
| Employee Name | `cf_employee_name1` | master → dra_attendance_location | optional | |
| Type of Leave | `cf_type_of_leave` | dropdown | **required** | General / Emergency / Medical |
| Leave Start Date | `cf_leave_start_date` | date | optional | For General leave |
| Leave end Date General | `cf_leave_end_date` | date | optional | For General leave |
| Sick / Emergency Leave Start Date | `cf_sick___emergency_leave_start_date` | date | optional | For Emergency/Medical |
| Description for the leave | `cf_description_for_the_leave` | text | optional | Reason for leave |
| Approval of leave | `cf_approval_of_leave` | dropdown | required (Approval stage) | Approve / Decline |

### Create Lead — Critical Requirement

`create_lead` on pipeline 7735 **requires a top-level `name` parameter**. Without it, the draft fails with "Name can't be blank".

**✅ Working example:**
```python
create_lead(pipeline_id=7735, 
    name="Nishant Ranka-2026-JUL",
    field_values={
        "cf_employee_name1": "Nishant Ranka",
        "cf_type_of_leave": "General",
        "cf_leave_start_date": "2026-07-30",
        "cf_leave_end_date": "2026-07-31",
        "cf_no_of_days_leave_for_general": 2,
        "cf_description_for_the_leave": "I am going on a holiday."
    })
```

**❌ Fails (missing `name`):**
```python
create_lead(pipeline_id=7735, 
    field_values={
        "cf_employee_name1": "Nishant Ranka",
        # ...same fields...
        "cf_identifier": "Nishant Ranka-2026-JUL"  # cf_identifier alone doesn't help
    })
# → Draft fails: "Name can't be blank"
```

### Automations

- On entry at Start: Sets assignee to user 41 (Nishant Ranka) and user 11652 (HR)
- On Approval with Approve + General type: Creates monthly attendance record, progresses to Retired
- On Approval with Decline: Jumps to Retired
- On Approval with Approve + Emergency/Medical: Goes to Update of documents for sick Leave stage

### Existing Record Example (Bharat H - Medical Leave)
```
Type of Leave: Medical
Sick / Emergency Leave Start Date: 2026-06-18
Description: I am suffering from cold and cough...
Earned Leaves: 1
Medical Leaves: 1
```

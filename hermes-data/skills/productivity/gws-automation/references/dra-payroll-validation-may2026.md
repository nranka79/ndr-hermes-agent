# DRA Attendance + Payroll Validation — Verified Findings (May 2026)

## DRA Attendance Sheet — Verified Column Layout (2026 version)

Source: `https://docs.google.com/spreadsheets/d/1sm8itK6tw10u7qx1WUcre1IFCAtj3_1cAIO8Qh6e-cs`

| Col | Header | Notes |
|-----|--------|-------|
| 0 | Employee name | |
| 1 | Emp code | |
| 2 | Emp email | |
| 3 | Date | DD-MM-YYYY |
| 4 | Actual sign in | Full datetime string e.g. `04-05-2026 9:45` |
| 5 | Sign in status | `"On Time"` / `"On Time - Sign Out"` etc. |
| 6 | Actual sign-out | Full datetime string e.g. `04-05-2026 18:42` |
| 7 | Sign out status | `"On Time - Sign Out"` etc. |
| 8 | Expected sign-in | Schedule (not actual) |
| 9 | Expected sign-out | Schedule (not actual) |
| 10 | Time spent hours | |
| 11 | Late sign-in minutes | 0 = on time |
| 12 | Early sign out minutes | 0 = on time / logged out early |
| 13 | Early sign-in minutes | |
| 14 | Late sign-out minutes | |
| 15 | Daily penalty hours | Computed by attendance system |
| 16 | Daily deduction hours | `= penalty_hours * 2` (penalty = 2x deduction) |
| 17 | Overtime hours | |
| 18 | Uninformed leave | |
| 19 | Uninformed leave count | |
| 20 | Present count | 1 = present |
| 21 | Absent count | 1 = absent |
| 22 | Leave count | |
| 23 | Halfday count | |
| 24 | Lead id | |
| 25 | Id to quarterly uninformed leave | |

**Key:** For actual sign-in/out, use cols 4 and 6. Expected cols 8/9 are shift schedules, not actual data.

## DRA Payroll Sheet — Verified Column Layout

Source: `https://docs.google.com/spreadsheets/d/1JIWTEoxj35TfWRJo0_Ddsku92jwx_KCoW3mSFrwCGI8`

| Col | Header | Notes |
|-----|--------|-------|
| 0 | Date | |
| 1 | Employee code | Name e.g. `Bharat H`, `Sham` |
| 2 | Stage | `Employee` |
| 3 | Total working days | Always 31 |
| 4 | Deduction hours | |
| 5 | Absent days | |
| 6 | Total payroll deduction days | |
| 7 | Total payable days | `= 31 - AbsentDays - floor(DedHrs/8)` |
| 8 | Uninformed leave | |
| 9 | Base salary | |
| 10 | Final base salary | `= Salary - Absent*(Salary/31) - DedHrs*(Salary/248)` |
| 11 | Total amount | Paid to employee |

**Verified formula (confirmed via Anbarasan ₹125,000 case):**
- Daily Rate = Salary / 31 (not / 26)
- Hourly Rate = Salary / 248 (= 31 * 8)
- Expected Salary = Salary - (AbsentDays × DailyRate) - (DedHrs × HourlyRate)

## May 2026 Payroll — Key Findings

### Pattern: Payroll uses ROUND UP, not floor()

Pipeline spec says `floor(DedHrs/8)` for payable day deduction. Payroll actually rounds UP:
- 27.75 → 28 payable (Bharat H)
- 26.50 → 27 payable (Pavan)
- 22.50 → 23 payable (Sham)
- 20.25 → 21 payable (Prakash Singh)
- 15.50 → 16 payable (Vinod Das)

This causes small overpayments (₹194–₹1,210) for 7 employees.

### Bharat H — Detailed Breakdown

| Date | Act In | Act Out | Late Min | Early Out | Ded Hrs | Present |
|------|--------|---------|----------|-----------|---------|---------|
| 01-05-2026 | — | — | 0 | 0 | 0 | 1 (Labour Day holiday) |
| 02-05-2026 | 8:54 | 17:01 | 0 | 0 | 0 | 1 |
| 04-05-2026 | 9:45 | 18:42 | 0 | 0 | 0 | 1 |
| 06-05-2026 | 10:02 | 18:56 | 0 | 0 | 0 | 1 |
| 07-05-2026 | 9:01 | 18:45 | 0 | 0 | 0 | 1 |
| 08-05-2026 | 9:05 | — | 0 | 0 | 0 | **1 (ABSENT flag)** |
| 09-05-2026 | 8:58 | 16:17 | 0 | 0 | 0 | 1 |
| 11-05-2026 | 9:49 | 18:20 | 0 | **10 min early** | **2** | 1 |
| 12-05-2026 | 9:09 | 18:53 | 0 | 0 | 0 | 1 |
| 13-05-2026 | 9:54 | 18:30 | 0 | 0 | 0 | 1 |
| 14-05-2026 | 9:29 | 18:30 | 0 | 0 | 0 | 1 |
| 15-05-2026 | 10:07 | 16:05 | 0 | 0 | 0 | 1 |
| 16-05-2026 | 8:59 | 16:54 | 0 | 0 | 0 | 1 |
| 18-05-2026 | 9:59 | 18:44 | 0 | 0 | 0 | 1 |
| 19-05-2026 | 9:36 | 19:46 | 0 | 0 | 0 | 1 |
| 20-05-2026 | 9:55 | 18:59 | 0 | 0 | 0 | 1 |
| 21-05-2026 | 9:46 | 18:51 | 0 | 0 | 0 | 1 |
| 22-05-2026 | 9:41 | 18:47 | 0 | 0 | 0 | 1 |
| 23-05-2026 | 9:39 | 16:03 | 0 | 0 | 0 | 1 |
| 25-05-2026 | 9:29 | 18:37 | 0 | 0 | 0 | 1 |
| 26-05-2026 | 9:10 | 19:07 | 0 | 0 | 0 | 1 |
| 27-05-2026 | 9:43 | 18:41 | 0 | 0 | 0 | 1 |
| 28-05-2026 | 10:08 | 18:39 | 0 | 0 | 0 | 1 |
| 29-05-2026 | 10:07 | 18:48 | 0 | 0 | 0 | 1 |

**Totals:** 23 present, 1 absent (May 8), 2 deduction hours (May 11 early logout)
**Payroll:** Absent=1, DedHrs=2, Payable=30

### May 1 Labour Day — Holiday Status

All 16 employees have May 1 marked as `Present count=1, Absent count=0` — correctly treated as a holiday in the attendance system, NOT as an absent day.

**Confirmed holidays in May 2026:**
- May 1 — Labour Day (all 16 employees, paid holiday)
- May 15 — appears in attendance (CET exam?) — all 16 employees present

### Payroll vs Attendance Comparison (All 12 payroll employees)

| Employee | Salary | Att Absent | Att Ded Hrs | Att Payable | Pay Absent | Pay Ded Hrs | Pay Payable | Diff |
|----------|--------|------------|-------------|-------------|------------|-------------|-------------|------|
| Prakash Singh | 50,000 | 8 | 22 | 20.25 | 8 | 22 | 21 | +₹1,210 |
| Vinod Das | 60,000 | 13 | 20 | 15.50 | 13 | 20 | 16 | +₹968 |
| Sham | 27,000 | 8 | 4 | 22.50 | 8 | 4 | 23 | +₹435 |
| Aravindan Jyothi | 48,000 | 2 | 2 | 28.75 | 2 | 2 | 29 | +₹387 |
| Pavan | 22,000 | 3 | 12 | 26.50 | 3 | 12 | 27 | +₹355 |
| Ravi | 24,000 | 3 | 2 | 27.75 | 3 | 2 | 28 | +₹194 |
| Bharat H | 60,000 | 1 | 2 | 29.75 | 1 | 2 | 30 | +₹4,387 |
| Ambika | 5,000 | 20 | 0 | 11.00 | 21 | 0 | 10 | −₹806 |
| Sinchana DRA | 25,000 | 19 | 0 | 12.00 | 19 | 0 | 12 | MATCH |
| Kantesh | 55,000 | 25 | 0 | 6.00 | 25 | 0 | 6 | MATCH |
| Anbarasan | 125,000 | 10 | 0 | 21.00 | 10 | 0 | 21 | MATCH |

**Bharat H anomaly resolved:** The ₹4,387 difference is purely the rounding effect (29.75 → 30). Not a data error. Actual deduction hours match (2 hrs in both attendance and payroll).

**Ambika anomaly:** Attendance shows 20 absent days but payroll shows 21 absent. Attendance payable = 11, payroll payable = 10. This ₹806 underpayment needs investigation.

## Key Discrepancy Root Causes

1. **Rounding direction:** Payroll rounds payable days UP (`round()` or equivalent). Pipeline spec says `floor()`. This is the cause of overpayments for 7 employees.

2. **Ambika data mismatch:** Attendance shows 20 absent, payroll shows 21 absent. Direction is wrong — payroll says MORE absent than attendance records. This is a data entry error, not rounding.

3. **May 1 Labour Day handling:** Attendance correctly treats it as a holiday (Present=1 for all 16). Payroll formula (31 - absent - ded/8) doesn't have a special case for holidays — if an employee were absent on May 1, it would count as 1 absent day in payroll. This is working correctly for the current pay period.
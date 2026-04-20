# CMU University Library – Room Reservation System
### BIS 698 – Information Systems Capstone | Central Michigan University | Spring 2026

A desktop application built with Python and CustomTkinter for managing library study room reservations at Charles V. Park Library, CMU.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Login Credentials](#login-credentials)
- [Sample Data Summary](#sample-data-summary)
- [Features Overview](#features-overview)
- [Password Reset Flow](#password-reset-flow)
- [Database Schema](#database-schema)
- [Notes](#notes)

---

## Tech Stack

| Component      | Technology                        |
|---------------|-----------------------------------|
| UI Framework  | Python 3.12 + CustomTkinter       |
| Database      | MySQL (CMU server)                |
| Charts        | Matplotlib                        |
| Reports       | openpyxl (Excel), reportlab (PDF) |
| Date Picker   | tkcalendar                        |
| Timezone      | pytz                              |
| Images        | Pillow                            |

---

## Project Structure

```
BIS698_project/
├── main.py                        # Entry point — run this to start the app
├── connect_db.py                  # MySQL connection handler
├── credentials.py                 # DB credentials (not committed to git)
├── create_db.py                   # Creates all 6 database tables
├── BIS698_Sample_Data_Script.sql  # Full DB script — tables and sample data
├── requirements.txt               # Python dependencies
├── assets/
│   ├── ActionC_maroongold.png
│   └── reading-sunlit-library.jpg
├── components/
│   ├── header.py
│   ├── sidebar.py
│   └── date_picker.py
└── screens/
    ├── login_screen.py
    ├── signup_screen.py
    ├── forgot_password_screen.py
    ├── student_dashboard.py
    ├── browse_rooms.py
    ├── reservations.py
    ├── violations_student.py
    ├── profile_page.py
    ├── manager_dashboard.py
    ├── manage_rooms.py
    ├── manage_rules_violations.py
    ├── check_violations.py
    └── reports.py
```

---

## Prerequisites

- Python 3.10 or higher
- MySQL Workbench
- CMU VPN — connect via FortiClient to CMich before launching the app

---

## Setup Instructions

**Step 1 — Install dependencies:**

Open a terminal inside the project folder and run:

```bash
pip install -r requirements.txt
```

**Step 2 — Create credentials.py:**

Create a file named `credentials.py` in the project root:

```python
DB_HOST     = "141.209.241.57"
DB_PORT     = 3306
DB_NAME     = "BIS698WSpring26_7"
DB_USER     = "your_username"
DB_PASSWORD = "your_password"
```

> This file is excluded from git. Do not commit it.

---

## Database Setup

> Connect to the CMU VPN before running any database commands.

**Step 1 — Create the tables:**

Run the following command to create all 6 database tables:

```bash
python create_db.py
```

This sets up the empty tables. The app is ready to use at this point.
You can sign up as a student or log in with a seeded admin account.

**Step 2 — Load sample data (optional):**

If you want the application pre-populated with realistic data for testing
and demonstration purposes, open MySQL Workbench, connect to the CMU server,
open `BIS698_Sample_Data_Script.sql` and run it.

The script drops and recreates all tables then inserts 119 users, 17 rooms,
254 reservations, 220 check-ins, and 75 violations covering January to April 2026.

**If the database already has data from a previous run:**

The TRUNCATE block is available as comments at the top of `BIS698_Sample_Data_Script.sql`.
Uncomment those lines and run them in MySQL Workbench first to clear existing records,
then run the full script again from the beginning.

---

## Running the Application

Make sure the CMU VPN is connected, then run:

```bash
python main.py
```

The application opens at 1100×750. It can be resized or maximized.

---

## Login Credentials

**Admin accounts:**

| Name             | Email                       | Password  |
|-----------------|-----------------------------|-----------|
| Library Admin    | admin@cmich.edu             | Admin@123 |
| John Manager     | john.manager@cmich.edu      | Admin@123 |
| Sarah Supervisor | sarah.supervisor@cmich.edu  | Admin@123 |

**Student accounts:**

| Name           | Email               | Password    |
|---------------|---------------------|-------------|
| Showry Kata    | showry1k@cmich.edu  | Showry@1799 |
| Kiran Student  | kiran1k@cmich.edu   | Student@123 |
| James Anderson | ander1jm@cmich.edu  | Student@123 |

> All other students in the sample data use `Student@123` as their password.

**Suspended accounts (for testing the suspension flow):**

| Name         | Email              | Password    |
|-------------|---------------------|-------------|
| Mason Harris | harri8ma@cmich.edu  | Student@123 |
| Jacob Allen  | allen1ja@cmich.edu  | Student@123 |
| Daniel Baker | baker4da@cmich.edu  | Student@123 |

---

## Sample Data Summary

| Table        | Records | Notes                                    |
|-------------|---------|------------------------------------------|
| Users        | 119     | 6 admins + 113 students                  |
| Rooms        | 17      | Real Charles V. Park Library rooms       |
| Rules        | 3       | Rule set 3 is the currently active policy|
| Reservations | 254     | Jan–Apr 2026, all statuses               |
| Check_Ins    | 220     | Student and admin-override records       |
| Violations   | 75      | No-show and late cancellation violations |

**Rooms included:**

| Category          | Room Numbers                                                    | Floor | Capacity |
|------------------|------------------------------------------------------------------|-------|----------|
| Projector Room    | 211E, 211W                                                      | 2     | 20       |
| Group Study Room  | 207, 208, 307, 308                                              | 2–3   | 5        |
| Single Study Room | 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336          | 3     | 1        |

---

## Features Overview

**Student:**
- Browse available rooms by category with time slot selection
- Make reservations with full validation (conflicts, cooldown, daily limits)
- Check in within the 15-minute grace period
- Cancel reservations (late cancellations generate violations)
- View reservation history and filter by status
- View personal violations and penalty point total
- Edit profile (phone number, date of birth)
- Change password via the forgot password screen

**Admin:**
- Manager Dashboard with live charts (room usage, penalty distribution, violations trend) and student/date filters
- Manage rooms — add, edit, update room status
- Manage reservation policy rule sets
- Reset student passwords to a temporary password
- View and filter all student violations, edit and resolve them
- Generate and download reports as TXT, CSV, Excel, or PDF

---

## Password Reset Flow

1. Admin opens **Manage Rules** → clicks **Reset Student Password**
2. Searches for a student, selects them, clicks **Reset Password**
3. Student's password is set to the temporary password `mypass`
4. Student tries to log in with `mypass`
5. A popup appears notifying them of the temporary password
6. Student clicks **Change My Password** → directed to Forgot Password screen
7. Student enters `mypass` as the current password and sets a new one
8. Student logs in normally with the new password going forward

---

## Database Schema

Six tables with the following relationships:

```
Users
 ├── Reservations  ──── Check_Ins
 │         └──────────── Violations
 └── (admin) resolves Violations

Rules ──── Reservations
Rooms  ──── Reservations
```

All passwords are stored as SHA2-256 hashes.
The `password_reset_required` flag on Users triggers the forced password change flow.

---

## Notes

- CMU VPN must be active for the app to connect to the database
- A background thread checks for no-shows every 5 minutes automatically
- Reservation times are validated in EST timezone using pytz
- Maximum booking: 2 hours per reservation, 3 hours total per day
- Suspension threshold: 10 penalty points triggers a 14-day account suspension

---

*BIS 698 Capstone | Lourdu Bala Showry Kata | Central Michigan University | Spring 2026*
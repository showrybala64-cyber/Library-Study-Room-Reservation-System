# 📚 Library Study Room Reservation System

### *No more walking to the library to find every room taken. Book your spot in seconds.*

> A full-stack desktop application built for **Central Michigan University** that allows students to browse, reserve, and manage library study rooms — with a complete admin panel for room management, violation tracking, and usage reporting.

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-UI%20Framework-blue?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=for-the-badge)]()
[![Course](https://img.shields.io/badge/Course-BIS%20698%20%7C%20CMU-maroon?style=for-the-badge)]()

---

## 🎯 The Problem It Solves

CMU students waste time physically checking library rooms only to find them occupied. There is no centralized system for viewing availability, making reservations, or enforcing room usage policies.

**This system fixes that** — a fully functional desktop app with role-based access, real-time room availability, booking management, and admin oversight all in one place.

---

## ✨ Features

### 👨‍🎓 Student Role
| Feature | Description |
|---------|-------------|
| 🔐 **Secure Login and Signup** | @cmich.edu email restriction, real-time password validation, account lockout after failed attempts |
| 🗓️ **Browse and Reserve Rooms** | View available rooms by date/time, smart room-number dropdowns |
| 📋 **My Reservations** | View, check-in, and cancel active bookings |
| ⚠️ **Violations Tracker** | View personal violation history and status |
| 👤 **Profile Management** | Update personal info and account settings |

### 🛠️ Admin Role
| Feature | Description |
|---------|-------------|
| 🏠 **Room Management** | Add, edit, deactivate rooms and set capacity/rules |
| 📊 **Usage Reports** | Reservation trends and room utilization analytics (Matplotlib/Seaborn charts coming soon) |
| ⚖️ **Violations Management** | Review, flag, and resolve student violations |
| 👥 **Student Oversight** | Monitor active reservations across all students |

---

## 🛠️ Tech Stack

```
Language        ->  Python 3.x
UI Framework    ->  CustomTkinter (modern dark-themed desktop UI)
Database        ->  MySQL (via mysql-connector-python)
Architecture    ->  MVC-style with persistent header/sidebar layout
Auth            ->  Role-based login routing (Student / Admin)
Security        ->  @cmich.edu email validation, password lockout, hashed credentials
```

---

## 📂 Project Structure

```
BIS698_project/
│
├── main.py                    # App entry point and role-based routing
├── connect_db.py              # MySQL connection handler
├── create_db.py               # Database schema initialization
├── BIS698_SQL_Script.sql      # Full SQL schema and seed data
├── requirements.txt           # Python dependencies
│
├── components/
│   ├── header.py              # Persistent top navigation bar
│   ├── sidebar.py             # Role-aware sidebar navigation
│   └── __init__.py
│
├── screens/
│   ├── login_screen.py        # Login with lockout protection
│   ├── signup_screen.py       # Student registration (@cmich.edu only)
│   ├── forgot_password_screen.py
│   ├── student_dashboard.py   # Student home screen
│   ├── manager_dashboard.py   # Admin home screen
│   ├── browse_rooms.py        # Room availability and booking
│   ├── reservations.py        # Reservation management
│   ├── manage_rooms.py        # Admin room CRUD
│   ├── manage_rules_violations.py
│   ├── check_violations.py    # Admin violation review
│   ├── violations_student.py  # Student violation history
│   ├── reports.py             # Usage analytics dashboard
│   ├── profile_page.py
│   └── __init__.py
│
└── assets/
    ├── ActionC_maroongold.png  # CMU branding
    ├── events_banner.png
    └── reading-sunlit-library.jpg
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL Server running locally
- pip

### Installation

```bash
git clone https://github.com/showrybala64-cyber/Library-Study-Room-Reservation-System.git
cd Library-Study-Room-Reservation-System
pip install -r requirements.txt
```

### Database Setup

```bash
mysql -u root -p < BIS698_SQL_Script.sql
```

Create a `.env` file in the root:
```env
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=library_reservation
```

### Run

```bash
python main.py
```

---

## 🗺️ Roadmap

- [x] Role-based login routing (Student / Admin)
- [x] Real-time password validation
- [x] @cmich.edu email restriction
- [x] Password lockout after failed attempts
- [x] Persistent header/sidebar architecture
- [x] Smart room-number dropdowns
- [x] Browse and reserve rooms
- [x] Reservations check-in and cancel
- [x] Admin room management
- [x] Violations tracking
- [ ] Matplotlib/Seaborn usage charts in Reports screen
- [ ] Line charts for reservation trends over time
- [ ] ERD updates and final documentation

---

## 👤 About the Author

**Lourdu Bala Showry Kata**
M.S. Information Systems (Data Analytics) — Central Michigan University | GPA: 3.98
3+ years of data analytics experience at Amazon | OPT | Available Immediately

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lourdu-bala-showry-k)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/showrybala64-cyber)

---

*Final project for BIS 698 — Graduate Capstone, Central Michigan University, Spring 2026.*

# BIS698_SQL_Script.sql
# CMU University Library Room Reservation System
# Standalone SQL Submission Script - Spring 2026

# SECTION 1: DROP TABLES

DROP TABLE IF EXISTS Check_Ins;
DROP TABLE IF EXISTS Violations;
DROP TABLE IF EXISTS Reservations;
DROP TABLE IF EXISTS Rules;
DROP TABLE IF EXISTS Rooms;
DROP TABLE IF EXISTS Users;


# SECTION 2: CREATE TABLES


# --- Table: Users ---
CREATE TABLE Users (
    user_id              INT AUTO_INCREMENT PRIMARY KEY,
    first_name           VARCHAR(50)   NOT NULL,
    last_name            VARCHAR(50)   NOT NULL,
    email                VARCHAR(100)  NOT NULL UNIQUE,
    phone_number         VARCHAR(20)   NULL,
    date_of_birth        DATE          NULL,
    password_hash        VARCHAR(255)  NOT NULL,
    role                 ENUM('student','admin') NOT NULL DEFAULT 'student',
    account_status       ENUM('active','suspended') NOT NULL DEFAULT 'active',
    penalty_points       INT           NOT NULL DEFAULT 0,
    suspended_until      DATETIME      NULL,
    created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at        DATETIME      NULL
);

# --- Table: Rooms ---
CREATE TABLE Rooms (
    room_id              INT AUTO_INCREMENT PRIMARY KEY,
    room_code            VARCHAR(20)   NOT NULL UNIQUE,
    room_name            VARCHAR(100)  NOT NULL,
    room_category        ENUM('Projector Room','Group Study Room','Single Study Room') NOT NULL,
    floor_number         INT           NOT NULL,
    room_number          VARCHAR(20)   NOT NULL,
    capacity             INT           NOT NULL,
    status               ENUM('available','maintenance','inactive') NOT NULL DEFAULT 'available',
    description          VARCHAR(255)  NOT NULL,
    created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

# --- Table: Rules ---
CREATE TABLE Rules (
    rule_set_id                  INT AUTO_INCREMENT PRIMARY KEY,
    is_active                    BOOLEAN  NOT NULL DEFAULT TRUE,
    effective_from               DATETIME NOT NULL,
    max_booking_minutes          INT      NOT NULL,
    checkin_grace_minutes        INT      NOT NULL,
    cooldown_minutes             INT      NOT NULL,
    cancel_cutoff_minutes        INT      NOT NULL,
    points_no_show               INT      NOT NULL,
    points_late_cancel           INT      NOT NULL,
    suspension_threshold_points  INT      NOT NULL,
    suspension_duration_days     INT      NOT NULL,
    created_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

# --- Table: Reservations ---
CREATE TABLE Reservations (
    reservation_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT          NOT NULL,
    room_id              INT          NOT NULL,
    reservation_date     DATE         NOT NULL,
    start_time           TIME         NOT NULL,
    end_time             TIME         NOT NULL,
    status               ENUM('reserved','checked_in','cancelled','no_show','completed') NOT NULL DEFAULT 'reserved',
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    canceled_at          DATETIME     NULL,
    canceled_by_user_id  INT          NULL,
    reason               VARCHAR(255) NULL,
    rule_set_id          INT          NOT NULL,
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (room_id)             REFERENCES Rooms(room_id),
    FOREIGN KEY (canceled_by_user_id) REFERENCES Users(user_id),
    FOREIGN KEY (rule_set_id)         REFERENCES Rules(rule_set_id)
);

# --- Table: Check_Ins ---
CREATE TABLE Check_Ins (
    checkin_id           INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id       INT NOT NULL UNIQUE,
    user_id              INT NOT NULL,
    checkin_time         DATETIME NOT NULL,
    method               ENUM('student_ui','admin_override') NOT NULL DEFAULT 'student_ui',
    recorded_by_user_id  INT NULL,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id)      REFERENCES Reservations(reservation_id),
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (recorded_by_user_id) REFERENCES Users(user_id)
);

# --- Table: Violations ---
CREATE TABLE Violations (
    violation_id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT          NOT NULL,
    reservation_id       INT          NOT NULL,
    violation_type       ENUM('no_show','late_cancel') NOT NULL,
    points_assessed      INT          NOT NULL,
    status               ENUM('active','resolved') NOT NULL DEFAULT 'active',
    notes                VARCHAR(255) NULL,
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at          DATETIME     NULL,
    resolved_by_user_id  INT          NULL,
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (reservation_id)      REFERENCES Reservations(reservation_id),
    FOREIGN KEY (resolved_by_user_id) REFERENCES Users(user_id)
);


# SECTION 3: INSERT DATA



# INSERT Users (3 admins + 30 students = 33 total)
# user_id 1-3  : admins
# user_id 4-33 : students


INSERT INTO Users
    (first_name, last_name, email, phone_number, date_of_birth,
     password_hash, role, account_status, penalty_points, suspended_until,
     created_at, last_login_at)
VALUES
# --- Admins ---
('Sarah',       'Johnson',   'sjohnson@cmich.edu',   '989-774-3310', '1985-03-15', SHA2('Password@123',256), 'admin',   'active',     0, NULL,                  '2025-08-01 08:00:00', '2026-04-04 09:15:00'),
('Michael',     'Chen',      'mchen@cmich.edu',       '989-774-3315', '1978-07-22', SHA2('Password@123',256), 'admin',   'active',     0, NULL,                  '2025-08-01 08:00:00', '2026-04-04 08:30:00'),
('Patricia',    'Williams',  'pwilliams@cmich.edu',   '989-774-3320', '1982-11-08', SHA2('Password@123',256), 'admin',   'active',     0, NULL,                  '2025-08-01 08:00:00', '2026-04-03 14:00:00'),
# --- Students (active, 0 penalty points) ---
('James',       'Anderson',  'ander1jm@cmich.edu',    '734-555-0101', '2003-05-12', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 11:00:00'),
('Emma',        'Thompson',  'thomp5em@cmich.edu',    '616-555-0102', '2004-01-30', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-03 14:30:00'),
('Ava',         'Taylor',    'taylo4av@cmich.edu',    '231-555-0106', '2004-03-14', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 08:00:00'),
('Olivia',      'Davis',     'davis7ol@cmich.edu',    '517-555-0104', '2003-12-05', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-01 15:00:00'),
('Sophia',      'White',     'white1so@cmich.edu',    '810-555-0108', '2003-11-22', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 10:30:00'),
('Isabella',    'Clark',     'clark2is@cmich.edu',    '734-555-0110', '2004-06-30', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-03 16:00:00'),
('Charlotte',   'Hall',      'hall7ch@cmich.edu',     '989-555-0114', '2004-08-03', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 12:00:00'),
('Amelia',      'Young',     'young4am@cmich.edu',    '269-555-0116', '2003-01-14', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-03 11:00:00'),
('Harper',      'King',      'king2ha@cmich.edu',     '947-555-0118', '2004-04-23', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 13:00:00'),
('Evelyn',      'Lopez',     'lopez3ev@cmich.edu',    '616-555-0120', '2003-07-16', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-02 16:00:00'),
('Abigail',     'Scott',     'scott5ab@cmich.edu',    '517-555-0122', '2004-10-20', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-03 10:00:00'),
('Emily',       'Adams',     'adams2em@cmich.edu',    '231-555-0124', '2003-02-25', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-02 11:00:00'),
('Elizabeth',   'Gonzalez',  'gonza1el@cmich.edu',    '810-555-0126', '2004-05-01', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 08:30:00'),
('Sofia',       'Carter',    'carte3so@cmich.edu',    '734-555-0128', '2003-09-09', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-03 15:00:00'),
('Scarlett',    'Perez',     'perez5sc@cmich.edu',    '248-555-0130', '2004-02-14', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 11:30:00'),
('Mia',         'Robinson',  'robin3mi@cmich.edu',    '248-555-0112', '2003-10-08', SHA2('Password@123',256), 'student', 'active',     0, NULL,                  '2025-09-02 10:00:00', '2026-04-04 09:00:00'),
# --- Students (active, with penalty points) ---
('Noah',        'Martinez',  'marti3no@cmich.edu',    '248-555-0103', '2002-09-18', SHA2('Password@123',256), 'student', 'active',     3, NULL,                  '2025-09-02 10:00:00', '2026-04-02 09:00:00'),
('Liam',        'Wilson',    'wilso2li@cmich.edu',    '989-555-0105', '2001-08-25', SHA2('Password@123',256), 'student', 'active',     6, NULL,                  '2025-09-02 10:00:00', '2026-03-31 10:00:00'),
('Ethan',       'Brown',     'brown6et@cmich.edu',    '269-555-0107', '2002-07-01', SHA2('Password@123',256), 'student', 'active',     9, NULL,                  '2025-09-02 10:00:00', '2026-03-28 13:00:00'),
('William',     'Lewis',     'lewis9wi@cmich.edu',    '616-555-0111', '2002-02-11', SHA2('Password@123',256), 'student', 'active',     6, NULL,                  '2025-09-02 10:00:00', '2026-04-01 11:00:00'),
('Benjamin',    'Walker',    'walke5be@cmich.edu',    '517-555-0113', '2001-12-19', SHA2('Password@123',256), 'student', 'active',     3, NULL,                  '2025-09-02 10:00:00', '2026-04-02 14:00:00'),
('Lucas',       'Hernandez', 'herna6lu@cmich.edu',    '810-555-0117', '2001-09-06', SHA2('Password@123',256), 'student', 'active',     6, NULL,                  '2025-09-02 10:00:00', '2026-03-30 15:00:00'),
('Henry',       'Wright',    'wrigh8he@cmich.edu',    '734-555-0119', '2002-11-30', SHA2('Password@123',256), 'student', 'active',     3, NULL,                  '2025-09-02 10:00:00', '2026-04-01 09:00:00'),
('Alexander',   'Hill',      'hill9al@cmich.edu',     '248-555-0121', '2001-03-04', SHA2('Password@123',256), 'student', 'active',     9, NULL,                  '2025-09-02 10:00:00', '2026-03-29 12:00:00'),
('Michael',     'Green',     'green7mi@cmich.edu',    '989-555-0123', '2002-06-07', SHA2('Password@123',256), 'student', 'active',     3, NULL,                  '2025-09-02 10:00:00', '2026-04-04 14:00:00'),
('Christopher', 'Nelson',    'nelso6ch@cmich.edu',    '947-555-0127', '2002-12-18', SHA2('Password@123',256), 'student', 'active',     6, NULL,                  '2025-09-02 10:00:00', '2026-03-31 14:00:00'),
('Matthew',     'Mitchell',  'mitch8ma@cmich.edu',    '616-555-0129', '2001-06-26', SHA2('Password@123',256), 'student', 'active',     3, NULL,                  '2025-09-02 10:00:00', '2026-04-01 13:00:00'),
# --- Students (suspended) ---
('Mason',       'Harris',    'harri8ma@cmich.edu',    '947-555-0109', '2001-04-17', SHA2('Password@123',256), 'student', 'suspended', 12, '2026-04-20 23:59:59', '2025-09-02 10:00:00', '2026-03-25 09:00:00'),
('Jacob',       'Allen',     'allen1ja@cmich.edu',    '231-555-0115', '2002-05-27', SHA2('Password@123',256), 'student', 'suspended', 15, '2026-04-15 23:59:59', '2025-09-02 10:00:00', '2026-03-22 10:00:00'),
('Daniel',      'Baker',     'baker4da@cmich.edu',    '269-555-0125', '2001-08-12', SHA2('Password@123',256), 'student', 'suspended', 12, '2026-04-10 23:59:59', '2025-09-02 10:00:00', '2026-03-20 08:00:00');


# INSERT Rooms (30 total)
# room_id  1- 3 : Floor 1 Group Study Rooms
# room_id  4- 7 : Floor 1 Single Study Rooms
# room_id  8- 9 : Floor 2 Projector Rooms (211E, 211W)
# room_id 10-11 : Floor 2 Group Study Rooms (207, 208)
# room_id 12-14 : Floor 2 Single Study Rooms
# room_id 15-16 : Floor 3 Group Study Rooms (307, 308)
# room_id 17-27 : Floor 3 Single Study Rooms (326-336)
# room_id 28-30 : Floor 4 Single Study Rooms


INSERT INTO Rooms
    (room_code, room_name, room_category, floor_number, room_number,
     capacity, status, description)
VALUES
# --- Floor 1: Group Study Rooms ---
('GRP-107',   'Group Study Room 107',           'Group Study Room',    1, '107',  5, 'available',   'First floor group study room with whiteboard and 5-seat round table'),
('GRP-108',   'Group Study Room 108',           'Group Study Room',    1, '108',  5, 'available',   'First floor group study room with wall-mounted display screen and 5 seats'),
('GRP-109',   'Group Study Room 109',           'Group Study Room',    1, '109',  5, 'maintenance', 'First floor group study room currently undergoing scheduled renovation'),
# --- Floor 1: Single Study Rooms ---
('SNG-120',   'Single Study Room 120',          'Single Study Room',   1, '120',  1, 'available',   'Quiet first floor single-occupancy study carrel with desktop power outlet'),
('SNG-121',   'Single Study Room 121',          'Single Study Room',   1, '121',  1, 'available',   'Quiet first floor single-occupancy study carrel with natural window lighting'),
('SNG-122',   'Single Study Room 122',          'Single Study Room',   1, '122',  1, 'available',   'Quiet first floor single-occupancy study carrel near main stairwell'),
('SNG-123',   'Single Study Room 123',          'Single Study Room',   1, '123',  1, 'inactive',    'First floor study carrel temporarily closed for electrical panel upgrade'),
# --- Floor 2: Projector Rooms ---
('PROJ-211E', 'Projector Room 211 East',        'Projector Room',      2, '211E', 20, 'available',  'Large east-wing presentation room with HD projector, whiteboard, and 20-seat conference table'),
('PROJ-211W', 'Projector Room 211 West',        'Projector Room',      2, '211W', 20, 'available',  'Large west-wing presentation room with dual HD projectors and 20-seat tiered layout'),
# --- Floor 2: Group Study Rooms ---
('GRP-207',   'Group Study Room 207',           'Group Study Room',    2, '207',  5, 'available',   'Second floor group study room with glass walls, whiteboard, and 5-seat round table'),
('GRP-208',   'Group Study Room 208',           'Group Study Room',    2, '208',  5, 'available',   'Second floor group study room with wall-mounted display screen and 5 seats'),
# --- Floor 2: Single Study Rooms ---
('SNG-226',   'Single Study Room 226',          'Single Study Room',   2, '226',  1, 'available',   'Second floor quiet study carrel with power strip and USB-C charging outlet'),
('SNG-227',   'Single Study Room 227',          'Single Study Room',   2, '227',  1, 'available',   'Second floor quiet study carrel with adjustable-height desk surface'),
('SNG-228',   'Single Study Room 228',          'Single Study Room',   2, '228',  1, 'available',   'Second floor quiet study carrel with ergonomic chair and task lighting'),
# --- Floor 3: Group Study Rooms ---
('GRP-307',   'Group Study Room 307',           'Group Study Room',    3, '307',  5, 'available',   'Third floor group study room with 55-inch smart TV display and 5 seats'),
('GRP-308',   'Group Study Room 308',           'Group Study Room',    3, '308',  5, 'available',   'Third floor group study room with acoustic soundproofing panels and 5-seat table'),
# --- Floor 3: Single Study Rooms 326-336 ---
('SNG-326',   'Single Study Room 326',          'Single Study Room',   3, '326',  1, 'available',   'Third floor quiet study carrel with campus view window and ergonomic seating'),
('SNG-327',   'Single Study Room 327',          'Single Study Room',   3, '327',  1, 'available',   'Third floor quiet study carrel with extended desk workspace and bookshelf'),
('SNG-328',   'Single Study Room 328',          'Single Study Room',   3, '328',  1, 'available',   'Third floor quiet study carrel with dedicated foldable laptop stand'),
('SNG-329',   'Single Study Room 329',          'Single Study Room',   3, '329',  1, 'available',   'Third floor quiet study carrel conveniently located near printing station'),
('SNG-330',   'Single Study Room 330',          'Single Study Room',   3, '330',  1, 'available',   'Third floor quiet study carrel with multi-outlet power strip access'),
('SNG-331',   'Single Study Room 331',          'Single Study Room',   3, '331',  1, 'maintenance', 'Third floor study carrel under scheduled maintenance and chair replacement'),
('SNG-332',   'Single Study Room 332',          'Single Study Room',   3, '332',  1, 'available',   'Third floor quiet study carrel with coat hook and under-desk storage'),
('SNG-333',   'Single Study Room 333',          'Single Study Room',   3, '333',  1, 'available',   'Third floor quiet study carrel equipped with small whiteboard panel'),
('SNG-334',   'Single Study Room 334',          'Single Study Room',   3, '334',  1, 'available',   'Third floor quiet study carrel in preferred corner location near elevator'),
('SNG-335',   'Single Study Room 335',          'Single Study Room',   3, '335',  1, 'available',   'Third floor quiet study carrel with adjustable LED task lamp'),
('SNG-336',   'Single Study Room 336',          'Single Study Room',   3, '336',  1, 'available',   'Third floor quiet study carrel adjacent to water fountain and restrooms'),
# --- Floor 4: Single Study Rooms ---
('SNG-426',   'Single Study Room 426',          'Single Study Room',   4, '426',  1, 'available',   'Fourth floor quiet study carrel with panoramic campus view and natural light'),
('SNG-427',   'Single Study Room 427',          'Single Study Room',   4, '427',  1, 'available',   'Fourth floor quiet study carrel in designated silent zone with noise dampening'),
('SNG-428',   'Single Study Room 428',          'Single Study Room',   4, '428',  1, 'available',   'Fourth floor quiet study carrel with extended natural lighting and skyline view');


# INSERT Rules (3 rule sets - only rule_set_id=3 is active)
# Policy evolved over time: shorter bookings and lighter
# penalties in 2025, expanded bookings in 2026.


INSERT INTO Rules
    (is_active, effective_from, max_booking_minutes, checkin_grace_minutes,
     cooldown_minutes, cancel_cutoff_minutes, points_no_show, points_late_cancel,
     suspension_threshold_points, suspension_duration_days, created_at)
VALUES
# --- Rule Set 1: Original policy, effective Spring 2025 (inactive) ---
(FALSE, '2025-01-01 00:00:00',  60, 10, 30, 60, 3, 1, 10,  7, '2024-12-15 09:00:00'),
# --- Rule Set 2: Updated policy, effective Fall 2025 (inactive) ---
(FALSE, '2025-08-15 00:00:00',  90, 15, 30, 30, 3, 2, 10, 14, '2025-08-01 09:00:00'),
# --- Rule Set 3: Current policy, effective Spring 2026 (active) ---
(TRUE,  '2026-01-01 00:00:00', 120, 15, 60, 30, 3, 2, 10, 14, '2025-12-20 09:00:00');


# INSERT Reservations (65 total)
#
# reservation_id  1-30 : status = 'checked_in'    (supports 30 Check_Ins)
# reservation_id 31-47 : status = 'no_show'       (supports 17 no_show Violations)
# reservation_id 48-62 : status = 'cancelled'     (supports 15 late_cancel Violations)
# reservation_id 63-65 : status = 'reserved'      (upcoming reservations)
#
# User reference:
#   admins  : 1=Sarah Johnson, 2=Michael Chen, 3=Patricia Williams
#   students: 4=James Anderson, 5=Emma Thompson, 6=Ava Taylor,
#             7=Olivia Davis,   8=Sophia White,  9=Isabella Clark,
#            10=Charlotte Hall, 11=Amelia Young, 12=Harper King,
#            13=Evelyn Lopez,   14=Abigail Scott,15=Emily Adams,
#            16=Elizabeth Gonzalez, 17=Sofia Carter, 18=Scarlett Perez,
#            19=Mia Robinson,   20=Noah Martinez, 21=Liam Wilson,
#            22=Ethan Brown,    23=William Lewis, 24=Benjamin Walker,
#            25=Lucas Hernandez,26=Henry Wright,  27=Alexander Hill,
#            28=Michael Green,  29=Christopher Nelson, 30=Matthew Mitchell,
#            31=Mason Harris (suspended),
#            32=Jacob Allen (suspended),
#            33=Daniel Baker (suspended)


INSERT INTO Reservations
    (user_id, room_id, reservation_date, start_time, end_time, status,
     created_at, updated_at, canceled_at, canceled_by_user_id, reason, rule_set_id)
VALUES

# checked_in reservations (1-30) - January through March 2026

( 4,  1, '2026-01-05', '09:00:00', '10:00:00', 'checked_in', '2026-01-02 14:00:00', '2026-01-05 09:07:00', NULL, NULL, NULL, 3),
( 5, 10, '2026-01-06', '10:00:00', '11:30:00', 'checked_in', '2026-01-03 09:30:00', '2026-01-06 10:05:00', NULL, NULL, NULL, 3),
( 6,  8, '2026-01-07', '14:00:00', '16:00:00', 'checked_in', '2026-01-04 11:00:00', '2026-01-07 14:10:00', NULL, NULL, NULL, 3),
( 7, 11, '2026-01-08', '11:00:00', '12:00:00', 'checked_in', '2026-01-05 10:00:00', '2026-01-08 11:03:00', NULL, NULL, NULL, 3),
( 8,  4, '2026-01-09', '13:00:00', '14:00:00', 'checked_in', '2026-01-06 08:00:00', '2026-01-09 13:08:00', NULL, NULL, NULL, 3),
( 9, 17, '2026-01-12', '15:00:00', '16:00:00', 'checked_in', '2026-01-09 15:30:00', '2026-01-12 15:12:00', NULL, NULL, NULL, 3),
(10, 18, '2026-01-13', '08:00:00', '09:30:00', 'checked_in', '2026-01-10 12:00:00', '2026-01-13 08:06:00', NULL, NULL, NULL, 3),
(11, 19, '2026-01-14', '16:00:00', '17:00:00', 'checked_in', '2026-01-11 09:00:00', '2026-01-14 16:04:00', NULL, NULL, NULL, 3),
(12, 12, '2026-01-15', '09:00:00', '10:00:00', 'checked_in', '2026-01-12 14:00:00', '2026-01-15 09:09:00', NULL, NULL, NULL, 3),
(13, 15, '2026-01-16', '10:00:00', '12:00:00', 'checked_in', '2026-01-13 11:00:00', '2026-01-16 10:07:00', NULL, NULL, NULL, 3),
(14, 16, '2026-01-19', '13:00:00', '14:30:00', 'checked_in', '2026-01-16 08:30:00', '2026-01-19 13:05:00', NULL, NULL, NULL, 3),
(15, 20, '2026-01-20', '11:00:00', '12:00:00', 'checked_in', '2026-01-17 10:00:00', '2026-01-20 11:11:00', NULL, NULL, NULL, 3),
(16, 21, '2026-01-21', '14:00:00', '15:00:00', 'checked_in', '2026-01-18 13:00:00', '2026-01-21 14:06:00', NULL, NULL, NULL, 3),
(17,  9, '2026-01-22', '09:00:00', '11:00:00', 'checked_in', '2026-01-19 09:00:00', '2026-01-22 09:03:00', NULL, NULL, NULL, 3),
(18, 23, '2026-01-23', '16:00:00', '17:00:00', 'checked_in', '2026-01-20 14:00:00', '2026-01-23 16:08:00', NULL, NULL, NULL, 3),
(19, 24, '2026-02-02', '10:00:00', '11:00:00', 'checked_in', '2026-01-30 10:00:00', '2026-02-02 10:04:00', NULL, NULL, NULL, 3),
(20, 25, '2026-02-03', '13:00:00', '14:00:00', 'checked_in', '2026-01-31 11:00:00', '2026-02-03 13:10:00', NULL, NULL, NULL, 3),
(21, 26, '2026-02-04', '09:00:00', '10:30:00', 'checked_in', '2026-02-01 09:00:00', '2026-02-04 09:07:00', NULL, NULL, NULL, 3),
(22, 27, '2026-02-05', '14:00:00', '15:00:00', 'checked_in', '2026-02-02 08:00:00', '2026-02-05 14:05:00', NULL, NULL, NULL, 3),
(23, 28, '2026-02-06', '11:00:00', '12:00:00', 'checked_in', '2026-02-03 10:00:00', '2026-02-06 11:09:00', NULL, NULL, NULL, 3),
(24,  2, '2026-02-09', '15:00:00', '17:00:00', 'checked_in', '2026-02-06 13:00:00', '2026-02-09 15:06:00', NULL, NULL, NULL, 3),
(25,  5, '2026-02-10', '10:00:00', '11:00:00', 'checked_in', '2026-02-07 11:00:00', '2026-02-10 10:03:00', NULL, NULL, NULL, 3),
(26,  6, '2026-02-11', '13:00:00', '14:00:00', 'checked_in', '2026-02-08 10:00:00', '2026-02-11 13:08:00', NULL, NULL, NULL, 3),
(27, 13, '2026-02-12', '08:00:00', '09:00:00', 'checked_in', '2026-02-09 09:00:00', '2026-02-12 08:05:00', NULL, NULL, NULL, 3),
(28, 14, '2026-03-02', '16:00:00', '18:00:00', 'checked_in', '2026-02-27 14:00:00', '2026-03-02 16:04:00', NULL, NULL, NULL, 3),
(29, 29, '2026-03-03', '09:00:00', '10:30:00', 'checked_in', '2026-02-28 10:00:00', '2026-03-03 09:11:00', NULL, NULL, NULL, 3),
(30, 30, '2026-03-04', '11:00:00', '12:00:00', 'checked_in', '2026-03-01 09:00:00', '2026-03-04 11:07:00', NULL, NULL, NULL, 3),
( 4,  1, '2026-03-05', '14:00:00', '16:00:00', 'checked_in', '2026-03-02 11:00:00', '2026-03-05 14:06:00', NULL, NULL, NULL, 3),
( 5, 10, '2026-03-09', '10:00:00', '11:00:00', 'checked_in', '2026-03-06 09:00:00', '2026-03-09 10:03:00', NULL, NULL, NULL, 3),
( 6,  8, '2026-03-10', '13:00:00', '14:30:00', 'checked_in', '2026-03-07 08:30:00', '2026-03-10 13:09:00', NULL, NULL, NULL, 3),

# no_show reservations (31-47)

(31, 11, '2026-01-10', '10:00:00', '11:00:00', 'no_show', '2026-01-07 11:00:00', '2026-01-11 08:00:00', NULL, NULL, NULL, 3),
(32, 15, '2026-01-17', '14:00:00', '15:00:00', 'no_show', '2026-01-14 09:00:00', '2026-01-18 08:00:00', NULL, NULL, NULL, 3),
(33, 16, '2026-01-24', '09:00:00', '10:00:00', 'no_show', '2026-01-21 10:00:00', '2026-01-25 08:00:00', NULL, NULL, NULL, 3),
(21,  4, '2026-01-26', '11:00:00', '12:00:00', 'no_show', '2026-01-23 14:00:00', '2026-01-27 08:00:00', NULL, NULL, NULL, 3),
(22, 17, '2026-01-27', '15:00:00', '16:00:00', 'no_show', '2026-01-24 09:30:00', '2026-01-28 08:00:00', NULL, NULL, NULL, 3),
(23, 18, '2026-01-28', '13:00:00', '14:00:00', 'no_show', '2026-01-25 11:00:00', '2026-01-29 08:00:00', NULL, NULL, NULL, 3),
(20, 19, '2026-01-29', '16:00:00', '17:00:00', 'no_show', '2026-01-26 10:00:00', '2026-01-30 08:00:00', NULL, NULL, NULL, 3),
(31,  1, '2026-02-16', '10:00:00', '11:00:00', 'no_show', '2026-02-13 11:00:00', '2026-02-17 08:00:00', NULL, NULL, NULL, 3),
(32,  2, '2026-02-17', '14:00:00', '15:00:00', 'no_show', '2026-02-14 09:00:00', '2026-02-18 08:00:00', NULL, NULL, NULL, 3),
(33,  9, '2026-02-18', '09:00:00', '10:30:00', 'no_show', '2026-02-15 10:00:00', '2026-02-19 08:00:00', NULL, NULL, NULL, 3),
(31, 20, '2026-02-23', '11:00:00', '12:00:00', 'no_show', '2026-02-20 13:00:00', '2026-02-24 08:00:00', NULL, NULL, NULL, 3),
(32, 21, '2026-02-24', '15:00:00', '16:00:00', 'no_show', '2026-02-21 09:00:00', '2026-02-25 08:00:00', NULL, NULL, NULL, 3),
(33, 23, '2026-02-25', '08:00:00', '09:00:00', 'no_show', '2026-02-22 11:00:00', '2026-02-26 08:00:00', NULL, NULL, NULL, 3),
(21, 24, '2026-03-11', '10:00:00', '11:00:00', 'no_show', '2026-03-08 14:00:00', '2026-03-12 08:00:00', NULL, NULL, NULL, 3),
(22, 25, '2026-03-12', '13:00:00', '14:00:00', 'no_show', '2026-03-09 09:30:00', '2026-03-13 08:00:00', NULL, NULL, NULL, 3),
(23, 26, '2026-03-13', '16:00:00', '17:00:00', 'no_show', '2026-03-10 11:00:00', '2026-03-14 08:00:00', NULL, NULL, NULL, 3),
(20, 27, '2026-03-16', '09:00:00', '10:00:00', 'no_show', '2026-03-13 10:00:00', '2026-03-17 08:00:00', NULL, NULL, NULL, 3),

# cancelled reservations (48-62) - late cancellations (within 30 min of start)

( 7, 12, '2026-01-12', '11:00:00', '12:00:00', 'cancelled', '2026-01-09 10:00:00', '2026-01-12 10:42:00', '2026-01-12 10:42:00',  7, 'Late cancellation - schedule conflict', 3),
( 9, 13, '2026-01-19', '14:00:00', '15:00:00', 'cancelled', '2026-01-16 11:00:00', '2026-01-19 13:38:00', '2026-01-19 13:38:00',  9, 'Late cancellation - class ran over', 3),
(11, 14, '2026-01-26', '09:00:00', '10:00:00', 'cancelled', '2026-01-23 09:00:00', '2026-01-26 08:45:00', '2026-01-26 08:45:00', 11, 'Late cancellation - transportation issue', 3),
(12, 28, '2026-02-02', '15:00:00', '16:00:00', 'cancelled', '2026-01-30 14:00:00', '2026-02-02 14:35:00', '2026-02-02 14:35:00', 12, 'Late cancellation - study group disbanded', 3),
(13, 29, '2026-02-09', '10:00:00', '11:00:00', 'cancelled', '2026-02-06 10:00:00', '2026-02-09 09:48:00', '2026-02-09 09:48:00', 13, 'Late cancellation - illness', 3),
(14, 30, '2026-02-16', '13:00:00', '14:00:00', 'cancelled', '2026-02-13 12:00:00', '2026-02-16 12:40:00', '2026-02-16 12:40:00', 14, 'Late cancellation - schedule conflict', 3),
(15,  4, '2026-02-23', '11:00:00', '12:00:00', 'cancelled', '2026-02-20 11:00:00', '2026-02-23 10:42:00', '2026-02-23 10:42:00', 15, 'Late cancellation - exam rescheduled', 3),
(16,  5, '2026-03-02', '14:00:00', '15:00:00', 'cancelled', '2026-02-27 13:00:00', '2026-03-02 13:35:00', '2026-03-02 13:35:00', 16, 'Late cancellation - transportation issue', 3),
(17,  6, '2026-03-09', '09:00:00', '10:00:00', 'cancelled', '2026-03-06 09:00:00', '2026-03-09 08:45:00', '2026-03-09 08:45:00', 17, 'Late cancellation - class ran over', 3),
(18, 10, '2026-03-16', '15:00:00', '16:00:00', 'cancelled', '2026-03-13 14:00:00', '2026-03-16 14:38:00', '2026-03-16 14:38:00', 18, 'Late cancellation - schedule conflict', 3),
(19, 11, '2026-03-23', '11:00:00', '12:00:00', 'cancelled', '2026-03-20 11:00:00', '2026-03-23 10:42:00', '2026-03-23 10:42:00', 19, 'Late cancellation - study group cancelled', 3),
(24, 15, '2026-03-30', '14:00:00', '15:00:00', 'cancelled', '2026-03-27 10:00:00', '2026-03-30 13:35:00', '2026-03-30 13:35:00', 24, 'Late cancellation - illness', 3),
(25, 16, '2026-04-06', '10:00:00', '11:00:00', 'cancelled', '2026-04-03 09:00:00', '2026-04-06 09:48:00', '2026-04-06 09:48:00', 25, 'Late cancellation - transportation issue', 3),
(26, 17, '2026-04-13', '13:00:00', '14:00:00', 'cancelled', '2026-04-10 12:00:00', '2026-04-13 12:40:00', '2026-04-13 12:40:00', 26, 'Late cancellation - exam conflict', 3),
(27, 18, '2026-04-20', '15:00:00', '16:00:00', 'cancelled', '2026-04-17 14:00:00', '2026-04-20 14:42:00', '2026-04-20 14:42:00', 27, 'Late cancellation - schedule conflict', 3),

# reserved (upcoming) reservations (63-65)

(28,  1, '2026-04-10', '10:00:00', '11:00:00', 'reserved',  '2026-04-07 11:00:00', '2026-04-07 11:00:00', NULL, NULL, NULL, 3),
(29, 10, '2026-04-11', '14:00:00', '15:30:00', 'reserved',  '2026-04-08 09:30:00', '2026-04-08 09:30:00', NULL, NULL, NULL, 3),
(30,  8, '2026-04-15', '09:00:00', '11:00:00', 'reserved',  '2026-04-04 10:00:00', '2026-04-04 10:00:00', NULL, NULL, NULL, 3);


# INSERT Check_Ins (30 total)
# One record per checked_in reservation (reservation_id 1-30)
# checkin_time is within the 15-minute grace period of start_time
# Most via student_ui; a few via admin_override


INSERT INTO Check_Ins
    (reservation_id, user_id, checkin_time, method, recorded_by_user_id, created_at)
VALUES
( 1,  4, '2026-01-05 09:07:00', 'student_ui',     NULL, '2026-01-05 09:07:00'),
( 2,  5, '2026-01-06 10:05:00', 'student_ui',     NULL, '2026-01-06 10:05:00'),
( 3,  6, '2026-01-07 14:10:00', 'student_ui',     NULL, '2026-01-07 14:10:00'),
( 4,  7, '2026-01-08 11:03:00', 'student_ui',     NULL, '2026-01-08 11:03:00'),
( 5,  8, '2026-01-09 13:08:00', 'student_ui',     NULL, '2026-01-09 13:08:00'),
( 6,  9, '2026-01-12 15:12:00', 'student_ui',     NULL, '2026-01-12 15:12:00'),
( 7, 10, '2026-01-13 08:06:00', 'student_ui',     NULL, '2026-01-13 08:06:00'),
( 8, 11, '2026-01-14 16:04:00', 'student_ui',     NULL, '2026-01-14 16:04:00'),
( 9, 12, '2026-01-15 09:09:00', 'student_ui',     NULL, '2026-01-15 09:09:00'),
(10, 13, '2026-01-16 10:07:00', 'admin_override',    1, '2026-01-16 10:07:00'),
(11, 14, '2026-01-19 13:05:00', 'student_ui',     NULL, '2026-01-19 13:05:00'),
(12, 15, '2026-01-20 11:11:00', 'student_ui',     NULL, '2026-01-20 11:11:00'),
(13, 16, '2026-01-21 14:06:00', 'student_ui',     NULL, '2026-01-21 14:06:00'),
(14, 17, '2026-01-22 09:03:00', 'student_ui',     NULL, '2026-01-22 09:03:00'),
(15, 18, '2026-01-23 16:08:00', 'student_ui',     NULL, '2026-01-23 16:08:00'),
(16, 19, '2026-02-02 10:04:00', 'student_ui',     NULL, '2026-02-02 10:04:00'),
(17, 20, '2026-02-03 13:10:00', 'admin_override',    2, '2026-02-03 13:10:00'),
(18, 21, '2026-02-04 09:07:00', 'student_ui',     NULL, '2026-02-04 09:07:00'),
(19, 22, '2026-02-05 14:05:00', 'student_ui',     NULL, '2026-02-05 14:05:00'),
(20, 23, '2026-02-06 11:09:00', 'student_ui',     NULL, '2026-02-06 11:09:00'),
(21, 24, '2026-02-09 15:06:00', 'student_ui',     NULL, '2026-02-09 15:06:00'),
(22, 25, '2026-02-10 10:03:00', 'student_ui',     NULL, '2026-02-10 10:03:00'),
(23, 26, '2026-02-11 13:08:00', 'student_ui',     NULL, '2026-02-11 13:08:00'),
(24, 27, '2026-02-12 08:05:00', 'student_ui',     NULL, '2026-02-12 08:05:00'),
(25, 28, '2026-03-02 16:04:00', 'student_ui',     NULL, '2026-03-02 16:04:00'),
(26, 29, '2026-03-03 09:11:00', 'student_ui',     NULL, '2026-03-03 09:11:00'),
(27, 30, '2026-03-04 11:07:00', 'admin_override',    3, '2026-03-04 11:07:00'),
(28,  4, '2026-03-05 14:06:00', 'student_ui',     NULL, '2026-03-05 14:06:00'),
(29,  5, '2026-03-09 10:03:00', 'student_ui',     NULL, '2026-03-09 10:03:00'),
(30,  6, '2026-03-10 13:09:00', 'student_ui',     NULL, '2026-03-10 13:09:00');


# INSERT Violations (32 total)
#
# violation_id  1-17 : no_show     (3 pts each) for reservation_id 31-47
# violation_id 18-32 : late_cancel (2 pts each) for reservation_id 48-62
#
# Resolved by admins: violations 4-7 and 14-16 (no_show),
#                     violations 18-20 (late_cancel)
# Active: remaining violations (includes all suspended users)


INSERT INTO Violations
    (user_id, reservation_id, violation_type, points_assessed, status,
     notes, created_at, resolved_at, resolved_by_user_id)
VALUES
# --- no_show violations (reservation_id 31-47) ---
# Suspended user Mason Harris (user 31)
(31, 31, 'no_show', 3, 'active',   'Student did not check in within grace period',                             '2026-01-10 11:30:00', NULL,                  NULL),
# Suspended user Jacob Allen (user 32)
(32, 32, 'no_show', 3, 'active',   'Student did not check in within grace period',                             '2026-01-17 15:30:00', NULL,                  NULL),
# Suspended user Daniel Baker (user 33)
(33, 33, 'no_show', 3, 'active',   'Student did not check in within grace period',                             '2026-01-24 10:30:00', NULL,                  NULL),
# Active student Liam Wilson (user 21) - resolved
(21, 34, 'no_show', 3, 'resolved', 'Student did not check in within grace period',                             '2026-01-26 12:30:00', '2026-02-02 10:00:00', 1),
# Active student Ethan Brown (user 22) - resolved
(22, 35, 'no_show', 3, 'resolved', 'Student did not check in within grace period',                             '2026-01-27 16:30:00', '2026-02-03 10:00:00', 2),
# Active student William Lewis (user 23) - resolved
(23, 36, 'no_show', 3, 'resolved', 'Student failed to appear for reserved time slot',                          '2026-01-28 14:30:00', '2026-02-04 10:00:00', 3),
# Active student Noah Martinez (user 20) - resolved
(20, 37, 'no_show', 3, 'resolved', 'Student did not check in within grace period',                             '2026-01-29 17:30:00', '2026-02-05 10:00:00', 1),
# Second offense - Mason Harris (user 31) still active
(31, 38, 'no_show', 3, 'active',   'Repeated no-show; student did not check in within grace period',           '2026-02-16 11:30:00', NULL,                  NULL),
# Second offense - Jacob Allen (user 32) still active
(32, 39, 'no_show', 3, 'active',   'Repeated no-show; student did not check in within grace period',           '2026-02-17 15:30:00', NULL,                  NULL),
# Second offense - Daniel Baker (user 33) still active
(33, 40, 'no_show', 3, 'active',   'Repeated no-show; student did not check in within grace period',           '2026-02-18 11:00:00', NULL,                  NULL),
# Third offense - Mason Harris (user 31)
(31, 41, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',          '2026-02-23 12:30:00', NULL,                  NULL),
# Third offense - Jacob Allen (user 32)
(32, 42, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',          '2026-02-24 16:30:00', NULL,                  NULL),
# Third offense - Daniel Baker (user 33)
(33, 43, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',          '2026-02-25 09:30:00', NULL,                  NULL),
# Active student Liam Wilson (user 21) - resolved
(21, 44, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',               '2026-03-11 11:30:00', '2026-03-18 09:00:00', 2),
# Active student Ethan Brown (user 22) - resolved
(22, 45, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',               '2026-03-12 14:30:00', '2026-03-19 09:00:00', 3),
# Active student William Lewis (user 23) - active
(23, 46, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',               '2026-03-13 17:30:00', NULL,                  NULL),
# Active student Noah Martinez (user 20) - active
(20, 47, 'no_show', 3, 'active',   'Student did not appear for reserved single study room',                    '2026-03-16 10:30:00', NULL,                  NULL),
# --- late_cancel violations (reservation_id 48-62) ---
# Olivia Davis (user 7) - resolved
( 7, 48, 'late_cancel', 2, 'resolved', 'Reservation cancelled less than 30 minutes before start time',         '2026-01-12 10:42:00', '2026-01-19 10:00:00', 1),
# Isabella Clark (user 9) - resolved
( 9, 49, 'late_cancel', 2, 'resolved', 'Reservation cancelled less than 30 minutes before start time',         '2026-01-19 13:38:00', '2026-01-26 10:00:00', 2),
# Amelia Young (user 11) - resolved
(11, 50, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-01-26 08:45:00', '2026-02-02 10:00:00', 3),
# Harper King (user 12) - active
(12, 51, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-02-02 14:35:00', NULL,                  NULL),
# Evelyn Lopez (user 13) - active
(13, 52, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-09 09:48:00', NULL,                  NULL),
# Abigail Scott (user 14) - active
(14, 53, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-02-16 12:40:00', NULL,                  NULL),
# Emily Adams (user 15) - active
(15, 54, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-23 10:42:00', NULL,                  NULL),
# Elizabeth Gonzalez (user 16) - active
(16, 55, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-03-02 13:35:00', NULL,                  NULL),
# Sofia Carter (user 17) - active
(17, 56, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-09 08:45:00', NULL,                  NULL),
# Scarlett Perez (user 18) - active
(18, 57, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-03-16 14:38:00', NULL,                  NULL),
# Mia Robinson (user 19) - active
(19, 58, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-23 10:42:00', NULL,                  NULL),
# Benjamin Walker (user 24) - active
(24, 59, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-03-30 13:35:00', NULL,                  NULL),
# Lucas Hernandez (user 25) - active
(25, 60, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-04-06 09:48:00', NULL,                  NULL),
# Henry Wright (user 26) - active
(26, 61, 'late_cancel', 2, 'active',   'Reservation cancelled less than 30 minutes before start time',         '2026-04-13 12:40:00', NULL,                  NULL),
# Alexander Hill (user 27) - active
(27, 62, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-04-20 14:42:00', NULL,                  NULL);



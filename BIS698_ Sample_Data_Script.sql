# BIS 698 - University Library Room Reservation System
# Central Michigan University - Spring 2026
# Complete Database Script - Table Creation and Sample Data
# Schema-independent: does not reference any specific schema name
# Run this script in one execution to recreate and populate the database


# Drop tables in correct order to respect foreign key constraints

DROP TABLE IF EXISTS Violations;
DROP TABLE IF EXISTS Check_Ins;
DROP TABLE IF EXISTS Reservations;
DROP TABLE IF EXISTS Rules;
DROP TABLE IF EXISTS Rooms;
DROP TABLE IF EXISTS Users;


# Create Users table
# Stores student and administrator accounts
# role: student or admin
# account_status: active or suspended
# penalty_points: accumulates from violations, triggers suspension at threshold

CREATE TABLE Users (
    user_id         INT           NOT NULL AUTO_INCREMENT,
    first_name      VARCHAR(50)   NOT NULL,
    last_name       VARCHAR(50)   NOT NULL,
    email           VARCHAR(100)  NOT NULL UNIQUE,
    phone_number    VARCHAR(20)   NULL,
    date_of_birth   DATE          NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    role            ENUM('student','admin') NOT NULL DEFAULT 'student',
    account_status  ENUM('active','suspended') NOT NULL DEFAULT 'active',
    penalty_points  INT           NOT NULL DEFAULT 0,
    suspended_until DATETIME      NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at   DATETIME      NULL,
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Create Rooms table
# Stores all reservable library study spaces
# room_category: Projector Room, Group Study Room, Single Study Room
# status: available, maintenance, inactive

CREATE TABLE Rooms (
    room_id       INT           NOT NULL AUTO_INCREMENT,
    room_code     VARCHAR(20)   NOT NULL UNIQUE,
    room_name     VARCHAR(100)  NOT NULL,
    room_category ENUM('Projector Room','Group Study Room','Single Study Room') NOT NULL,
    floor_number  INT           NOT NULL,
    room_number   VARCHAR(20)   NOT NULL,
    capacity      INT           NOT NULL,
    status        ENUM('available','maintenance','inactive') NOT NULL DEFAULT 'available',
    description   VARCHAR(255)  NOT NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Create Rules table
# Defines reservation policy parameters
# Only one rule set is active at a time (is_active = TRUE)
# New reservations always reference the currently active rule set

CREATE TABLE Rules (
    rule_set_id                 INT      NOT NULL AUTO_INCREMENT,
    is_active                   BOOLEAN  NOT NULL DEFAULT TRUE,
    effective_from              DATETIME NOT NULL,
    max_booking_minutes         INT      NOT NULL,
    checkin_grace_minutes       INT      NOT NULL,
    cooldown_minutes            INT      NOT NULL,
    cancel_cutoff_minutes       INT      NOT NULL,
    points_no_show              INT      NOT NULL,
    points_late_cancel          INT      NOT NULL,
    suspension_threshold_points INT      NOT NULL,
    suspension_duration_days    INT      NOT NULL,
    created_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (rule_set_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Create Reservations table
# Links a student to a room for a specific date and time window
# status: reserved, checked_in, cancelled, no_show, completed
# canceled_by_user_id: records who cancelled (student self-cancel or admin)
# rule_set_id: references the active rule set at time of booking

CREATE TABLE Reservations (
    reservation_id      INT          NOT NULL AUTO_INCREMENT,
    user_id             INT          NOT NULL,
    room_id             INT          NOT NULL,
    reservation_date    DATE         NOT NULL,
    start_time          TIME         NOT NULL,
    end_time            TIME         NOT NULL,
    status              ENUM('reserved','checked_in','cancelled','no_show','completed') NOT NULL DEFAULT 'reserved',
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    canceled_at         DATETIME     NULL,
    canceled_by_user_id INT          NULL,
    reason              VARCHAR(255) NULL,
    rule_set_id         INT          NOT NULL,
    PRIMARY KEY (reservation_id),
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (room_id)             REFERENCES Rooms(room_id),
    FOREIGN KEY (canceled_by_user_id) REFERENCES Users(user_id),
    FOREIGN KEY (rule_set_id)         REFERENCES Rules(rule_set_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Create Check_Ins table
# Records student arrival for a reservation
# One check-in per reservation enforced by UNIQUE constraint on reservation_id
# method: student_ui (self check-in) or admin_override (staff recorded)

CREATE TABLE Check_Ins (
    checkin_id          INT      NOT NULL AUTO_INCREMENT,
    reservation_id      INT      NOT NULL UNIQUE,
    user_id             INT      NOT NULL,
    checkin_time        DATETIME NOT NULL,
    method              ENUM('student_ui','admin_override') NOT NULL DEFAULT 'student_ui',
    recorded_by_user_id INT      NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (checkin_id),
    FOREIGN KEY (reservation_id)      REFERENCES Reservations(reservation_id),
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (recorded_by_user_id) REFERENCES Users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Create Violations table
# Records policy breaches tied to specific reservations
# violation_type: no_show or late_cancel
# status: active or resolved
# resolved_by_user_id: admin who resolved the violation

CREATE TABLE Violations (
    violation_id        INT          NOT NULL AUTO_INCREMENT,
    user_id             INT          NOT NULL,
    reservation_id      INT          NOT NULL,
    violation_type      ENUM('no_show','late_cancel') NOT NULL,
    points_assessed     INT          NOT NULL,
    status              ENUM('active','resolved') NOT NULL DEFAULT 'active',
    notes               VARCHAR(255) NULL,
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at         DATETIME     NULL,
    resolved_by_user_id INT          NULL,
    PRIMARY KEY (violation_id),
    FOREIGN KEY (user_id)             REFERENCES Users(user_id),
    FOREIGN KEY (reservation_id)      REFERENCES Reservations(reservation_id),
    FOREIGN KEY (resolved_by_user_id) REFERENCES Users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# Insert users
# user_id 1  : Library Admin     (admin)
# user_id 2  : John Manager      (admin)
# user_id 3  : Sarah Supervisor  (admin)
# user_id 4  : Robert Thompson   (admin)
# user_id 5  : Jennifer Martinez (admin)
# user_id 6  : David Robinson    (admin)
# user_id 7  : Showry Kata       (student - existing account)
# user_id 8  : Kiran Student     (student - existing account)
# user_id 9-31  : students with no violations
# user_id 32-51 : students with minor penalty points
# user_id 52 : Mason Harris  (suspended, 12 pts)
# user_id 53 : Jacob Allen   (suspended, 15 pts)
# user_id 54 : Daniel Baker  (suspended, 12 pts)

INSERT INTO Users (first_name, last_name, email, phone_number, date_of_birth, password_hash, role, account_status, penalty_points, suspended_until, created_at, last_login_at)
VALUES
('Library',     'Admin',      'admin@cmich.edu',            '989-774-3310', '1985-03-15', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-13 09:00:00'),
('John',        'Manager',    'john.manager@cmich.edu',     '989-774-3315', '1978-07-22', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-13 08:30:00'),
('Sarah',       'Supervisor', 'sarah.supervisor@cmich.edu', '989-774-3320', '1982-11-08', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-12 14:00:00'),
('Robert',      'Thompson',   'rthompson@cmich.edu',        '989-774-3325', '1980-04-12', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-13 09:00:00'),
('Jennifer',    'Martinez',   'jmartinez@cmich.edu',        '989-774-3330', '1983-09-20', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-13 10:00:00'),
('David',       'Robinson',   'drobinson@cmich.edu',        '989-774-3335', '1979-06-15', SHA2('Admin@123',256),    'admin',   'active',    0,  NULL,                  '2025-08-01 08:00:00', '2026-04-12 14:00:00'),
('Showry',      'Kata',       'showry1k@cmich.edu',         '586-808-6962', '2000-01-01', SHA2('Showry@1799',256),  'student', 'active',    0,  NULL,                  '2026-03-22 10:00:00', '2026-04-14 10:00:00'),
('Kiran',       'Student',    'kiran1k@cmich.edu',          '989-555-0008', '2002-05-15', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2026-03-22 10:00:00', '2026-04-13 11:00:00'),
('James',       'Anderson',   'ander1jm@cmich.edu',         '734-555-0101', '2003-05-12', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 11:00:00'),
('Emma',        'Thompson',   'thomp5em@cmich.edu',         '616-555-0102', '2004-01-30', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 14:30:00'),
('Ava',         'Taylor',     'taylo4av@cmich.edu',         '231-555-0106', '2004-03-14', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 08:00:00'),
('Olivia',      'Davis',      'davis7ol@cmich.edu',         '517-555-0104', '2003-12-05', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-11 15:00:00'),
('Sophia',      'White',      'white1so@cmich.edu',         '810-555-0108', '2003-11-22', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 10:30:00'),
('Isabella',    'Clark',      'clark2is@cmich.edu',         '734-555-0110', '2004-06-30', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 16:00:00'),
('Charlotte',   'Hall',       'hall7ch@cmich.edu',          '989-555-0114', '2004-08-03', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 12:00:00'),
('Amelia',      'Young',      'young4am@cmich.edu',         '269-555-0116', '2003-01-14', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 11:00:00'),
('Harper',      'King',       'king2ha@cmich.edu',          '947-555-0118', '2004-04-23', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 13:00:00'),
('Abigail',     'Scott',      'scott5ab@cmich.edu',         '517-555-0122', '2004-10-20', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 10:00:00'),
('Emily',       'Adams',      'adams2em@cmich.edu',         '231-555-0124', '2003-02-25', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-11 11:00:00'),
('Elizabeth',   'Gonzalez',   'gonza1el@cmich.edu',         '810-555-0126', '2004-05-01', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 08:30:00'),
('Sofia',       'Carter',     'carte3so@cmich.edu',         '734-555-0128', '2003-09-09', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 15:00:00'),
('Scarlett',    'Perez',      'perez5sc@cmich.edu',         '248-555-0130', '2004-02-14', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 11:30:00'),
('Mia',         'Robinson',   'robin3mi@cmich.edu',         '248-555-0112', '2003-10-08', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 09:00:00'),
('Grace',       'Cooper',     'coope4gr@cmich.edu',         '989-555-0132', '2004-11-19', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 10:00:00'),
('Lily',        'Morgan',     'morga5li@cmich.edu',         '269-555-0134', '2003-08-05', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-12 16:00:00'),
('Chloe',       'Murphy',     'murph3ch@cmich.edu',         '734-555-0136', '2004-04-28', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 09:30:00'),
('Zoe',         'Rivera',     'river4zo@cmich.edu',         '248-555-0138', '2003-06-17', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-11 10:00:00'),
('Penelope',    'Price',      'price7pe@cmich.edu',         '989-555-0140', '2004-09-03', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-12 11:00:00'),
('Nora',        'Patterson',  'patte3no@cmich.edu',         '269-555-0142', '2003-01-25', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 12:30:00'),
('Hannah',      'Flores',     'flore2ha@cmich.edu',         '734-555-0144', '2004-07-12', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 08:00:00'),
('Luna',        'Foster',     'foste2lu@cmich.edu',         '989-555-0148', '2004-12-09', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-12 09:00:00'),
('Stella',      'Bryant',     'brya1st@cmich.edu',          '269-555-0150', '2003-03-18', SHA2('Student@123',256),  'student', 'active',    0,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 11:00:00'),
('Noah',        'Martinez',   'marti3no@cmich.edu',         '248-555-0103', '2002-09-18', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 09:00:00'),
('Liam',        'Wilson',     'wilso2li@cmich.edu',         '989-555-0105', '2001-08-25', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-10 10:00:00'),
('Ethan',       'Brown',      'brown6et@cmich.edu',         '269-555-0107', '2002-07-01', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-08 13:00:00'),
('William',     'Lewis',      'lewis9wi@cmich.edu',         '616-555-0111', '2002-02-11', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-11 11:00:00'),
('Benjamin',    'Walker',     'walke5be@cmich.edu',         '517-555-0113', '2001-12-19', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 14:00:00'),
('Lucas',       'Hernandez',  'herna6lu@cmich.edu',         '810-555-0117', '2001-09-06', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-10 15:00:00'),
('Henry',       'Wright',     'wrigh8he@cmich.edu',         '734-555-0119', '2002-11-30', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-11 09:00:00'),
('Evelyn',      'Lopez',      'lopez3ev@cmich.edu',         '616-555-0120', '2003-07-16', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-12 16:00:00'),
('Alexander',   'Hill',       'hill9al@cmich.edu',          '248-555-0121', '2001-03-04', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-09 12:00:00'),
('Michael',     'Green',      'green7mi@cmich.edu',         '989-555-0123', '2002-06-07', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-13 14:00:00'),
('Christopher', 'Nelson',     'nelso6ch@cmich.edu',         '947-555-0127', '2002-12-18', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-02 10:00:00', '2026-04-10 14:00:00'),
('Matthew',     'Mitchell',   'mitch8ma@cmich.edu',         '616-555-0129', '2001-06-26', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-02 10:00:00', '2026-04-11 13:00:00'),
('Andrew',      'Rivera',     'river2an@cmich.edu',         '517-555-0131', '2003-07-08', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-05 10:00:00', '2026-04-11 14:00:00'),
('Jackson',     'Reed',       'reed7ja@cmich.edu',          '231-555-0133', '2002-03-22', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-05 10:00:00', '2026-04-11 14:00:00'),
('Sebastian',   'Bell',       'bell9se@cmich.edu',          '810-555-0135', '2001-12-10', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-05 10:00:00', '2026-04-10 11:00:00'),
('Aiden',       'Bailey',     'baile6ai@cmich.edu',         '616-555-0137', '2002-10-14', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-05 10:00:00', '2026-04-12 13:00:00'),
('Owen',        'Hughes',     'hughe2ow@cmich.edu',         '517-555-0139', '2001-02-28', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-05 10:00:00', '2026-04-13 15:00:00'),
('Logan',       'Long',       'long5lo@cmich.edu',          '231-555-0141', '2002-05-16', SHA2('Student@123',256),  'student', 'active',    6,  NULL,                  '2025-09-05 10:00:00', '2026-04-09 09:00:00'),
('Elijah',      'Foster',     'foste8el@cmich.edu',         '810-555-0143', '2001-11-07', SHA2('Student@123',256),  'student', 'active',    3,  NULL,                  '2025-09-05 10:00:00', '2026-04-11 15:00:00'),
('Mason',       'Harris',     'harri8ma@cmich.edu',         '947-555-0109', '2001-04-17', SHA2('Student@123',256),  'student', 'suspended', 12, '2026-04-20 23:59:59', '2025-09-02 10:00:00', '2026-03-25 09:00:00'),
('Jacob',       'Allen',      'allen1ja@cmich.edu',         '231-555-0115', '2002-05-27', SHA2('Student@123',256),  'student', 'suspended', 15, '2026-04-28 23:59:59', '2025-09-02 10:00:00', '2026-03-22 10:00:00'),
('Daniel',      'Baker',      'baker4da@cmich.edu',         '269-555-0125', '2001-08-12', SHA2('Student@123',256),  'student', 'suspended', 12, '2026-04-21 23:59:59', '2025-09-02 10:00:00', '2026-03-20 08:00:00');


# Insert library rooms
# room_id 1-2  : Projector Rooms  floor 2 capacity 20 (211E, 211W)
# room_id 3-4  : Group Study Rooms floor 2 capacity 5 (207, 208)
# room_id 5-6  : Group Study Rooms floor 3 capacity 5 (307, 308)
# room_id 7-17 : Single Study Rooms floor 3 capacity 1 (326-336)

INSERT INTO Rooms (room_code, room_name, room_category, floor_number, room_number, capacity, status, description)
VALUES
('PRJ-211E', 'Projector Room 211 East', 'Projector Room',    2, '211E', 20, 'available',   'East-wing presentation room with HD projector, whiteboard, and 20-seat conference layout'),
('PRJ-211W', 'Projector Room 211 West', 'Projector Room',    2, '211W', 20, 'available',   'West-wing presentation room with dual HD projectors and 20-seat tiered seating'),
('GRP-207',  'Group Study Room 207',    'Group Study Room',  2, '207',  5,  'available',   'Second floor group study room with glass walls, whiteboard, and 5-seat round table'),
('GRP-208',  'Group Study Room 208',    'Group Study Room',  2, '208',  5,  'available',   'Second floor group study room with wall-mounted display screen and 5 seats'),
('GRP-307',  'Group Study Room 307',    'Group Study Room',  3, '307',  5,  'available',   'Third floor group study room with 55-inch smart TV display and 5-seat table'),
('GRP-308',  'Group Study Room 308',    'Group Study Room',  3, '308',  5,  'available',   'Third floor group study room with acoustic soundproofing panels and 5-seat table'),
('SNG-326',  'Single Study Room 326',   'Single Study Room', 3, '326',  1,  'available',   'Third floor quiet study carrel with campus view window and ergonomic seating'),
('SNG-327',  'Single Study Room 327',   'Single Study Room', 3, '327',  1,  'available',   'Third floor quiet study carrel with extended desk workspace and bookshelf'),
('SNG-328',  'Single Study Room 328',   'Single Study Room', 3, '328',  1,  'available',   'Third floor quiet study carrel with dedicated foldable laptop stand'),
('SNG-329',  'Single Study Room 329',   'Single Study Room', 3, '329',  1,  'available',   'Third floor quiet study carrel conveniently located near printing station'),
('SNG-330',  'Single Study Room 330',   'Single Study Room', 3, '330',  1,  'available',   'Third floor quiet study carrel with multi-outlet power strip access'),
('SNG-331',  'Single Study Room 331',   'Single Study Room', 3, '331',  1,  'maintenance', 'Third floor study carrel under scheduled maintenance and chair replacement'),
('SNG-332',  'Single Study Room 332',   'Single Study Room', 3, '332',  1,  'available',   'Third floor quiet study carrel with coat hook and under-desk storage'),
('SNG-333',  'Single Study Room 333',   'Single Study Room', 3, '333',  1,  'available',   'Third floor quiet study carrel equipped with small whiteboard panel'),
('SNG-334',  'Single Study Room 334',   'Single Study Room', 3, '334',  1,  'available',   'Third floor quiet study carrel in preferred corner location near elevator'),
('SNG-335',  'Single Study Room 335',   'Single Study Room', 3, '335',  1,  'available',   'Third floor quiet study carrel with adjustable LED task lamp'),
('SNG-336',  'Single Study Room 336',   'Single Study Room', 3, '336',  1,  'available',   'Third floor quiet study carrel adjacent to water fountain and restrooms');


# Insert rule sets reflecting policy evolution across academic years
# rule_set_id 1: original policy Spring 2025 (inactive)
# rule_set_id 2: updated policy Fall 2025 (inactive)
# rule_set_id 3: current active policy Spring 2026
# All new reservations reference rule_set_id 3

INSERT INTO Rules (is_active, effective_from, max_booking_minutes, checkin_grace_minutes, cooldown_minutes, cancel_cutoff_minutes, points_no_show, points_late_cancel, suspension_threshold_points, suspension_duration_days, created_at)
VALUES
(FALSE, '2025-01-01 00:00:00',  60, 10, 30, 60, 3, 1, 10,  7, '2024-12-15 09:00:00'),
(FALSE, '2025-08-15 00:00:00',  90, 15, 30, 30, 3, 2, 10, 14, '2025-08-01 09:00:00'),
(TRUE,  '2026-01-01 00:00:00', 120, 15, 60, 30, 3, 2, 10, 14, '2025-12-20 09:00:00');


# Insert reservations spanning January through April 2026
# reservation_id 1-30  : status checked_in
# reservation_id 31-47 : status no_show
# reservation_id 48-62 : status cancelled (late cancellations)
# reservation_id 63-65 : status reserved  (upcoming bookings)
#
# Room reference:
# room_id 1=PRJ-211E  2=PRJ-211W  3=GRP-207   4=GRP-208
# room_id 5=GRP-307   6=GRP-308   7=SNG-326   8=SNG-327
# room_id 9=SNG-328  10=SNG-329  11=SNG-330  12=SNG-331
# room_id 13=SNG-332 14=SNG-333  15=SNG-334  16=SNG-335  17=SNG-336
#
# User reference:
# user_id 7=Showry  8=Kiran
# user_id 9-31  = students with no violations
# user_id 32-51 = students with minor violations
# user_id 52=Mason(suspended) 53=Jacob(suspended) 54=Daniel(suspended)

INSERT INTO Reservations (user_id, room_id, reservation_date, start_time, end_time, status, created_at, updated_at, canceled_at, canceled_by_user_id, reason, rule_set_id)
VALUES
# Checked-in reservations January 2026
(9,  7,  '2026-01-05', '09:00:00', '10:00:00', 'checked_in', '2026-01-02 14:00:00', '2026-01-05 09:07:00', NULL, NULL, NULL, 3),
(10, 3,  '2026-01-06', '10:00:00', '11:30:00', 'checked_in', '2026-01-03 09:30:00', '2026-01-06 10:05:00', NULL, NULL, NULL, 3),
(11, 1,  '2026-01-07', '14:00:00', '16:00:00', 'checked_in', '2026-01-04 11:00:00', '2026-01-07 14:10:00', NULL, NULL, NULL, 3),
(12, 8,  '2026-01-08', '11:00:00', '12:00:00', 'checked_in', '2026-01-05 10:00:00', '2026-01-08 11:03:00', NULL, NULL, NULL, 3),
(13, 4,  '2026-01-09', '13:00:00', '14:00:00', 'checked_in', '2026-01-06 08:00:00', '2026-01-09 13:08:00', NULL, NULL, NULL, 3),
(14, 9,  '2026-01-12', '15:00:00', '16:00:00', 'checked_in', '2026-01-09 15:30:00', '2026-01-12 15:12:00', NULL, NULL, NULL, 3),
(15, 2,  '2026-01-13', '08:00:00', '09:30:00', 'checked_in', '2026-01-10 12:00:00', '2026-01-13 08:06:00', NULL, NULL, NULL, 3),
(16, 10, '2026-01-14', '16:00:00', '17:00:00', 'checked_in', '2026-01-11 09:00:00', '2026-01-14 16:04:00', NULL, NULL, NULL, 3),
(17, 5,  '2026-01-15', '09:00:00', '10:00:00', 'checked_in', '2026-01-12 14:00:00', '2026-01-15 09:09:00', NULL, NULL, NULL, 3),
(18, 11, '2026-01-16', '10:00:00', '12:00:00', 'checked_in', '2026-01-13 11:00:00', '2026-01-16 10:07:00', NULL, NULL, NULL, 3),
(19, 6,  '2026-01-19', '13:00:00', '14:30:00', 'checked_in', '2026-01-16 08:30:00', '2026-01-19 13:05:00', NULL, NULL, NULL, 3),
(20, 13, '2026-01-20', '11:00:00', '12:00:00', 'checked_in', '2026-01-17 10:00:00', '2026-01-20 11:11:00', NULL, NULL, NULL, 3),
(21, 7,  '2026-01-21', '14:00:00', '15:00:00', 'checked_in', '2026-01-18 13:00:00', '2026-01-21 14:06:00', NULL, NULL, NULL, 3),
(22, 3,  '2026-01-22', '09:00:00', '11:00:00', 'checked_in', '2026-01-19 09:00:00', '2026-01-22 09:03:00', NULL, NULL, NULL, 3),
(23, 14, '2026-01-23', '16:00:00', '17:00:00', 'checked_in', '2026-01-20 14:00:00', '2026-01-23 16:08:00', NULL, NULL, NULL, 3),
# Checked-in reservations February 2026
(24, 8,  '2026-02-02', '10:00:00', '11:00:00', 'checked_in', '2026-01-30 10:00:00', '2026-02-02 10:04:00', NULL, NULL, NULL, 3),
(25, 4,  '2026-02-03', '13:00:00', '14:00:00', 'checked_in', '2026-01-31 11:00:00', '2026-02-03 13:10:00', NULL, NULL, NULL, 3),
(26, 1,  '2026-02-04', '09:00:00', '10:30:00', 'checked_in', '2026-02-01 09:00:00', '2026-02-04 09:07:00', NULL, NULL, NULL, 3),
(27, 15, '2026-02-05', '14:00:00', '15:00:00', 'checked_in', '2026-02-02 08:00:00', '2026-02-05 14:05:00', NULL, NULL, NULL, 3),
(28, 5,  '2026-02-06', '11:00:00', '12:00:00', 'checked_in', '2026-02-03 10:00:00', '2026-02-06 11:09:00', NULL, NULL, NULL, 3),
(29, 2,  '2026-02-09', '15:00:00', '17:00:00', 'checked_in', '2026-02-06 13:00:00', '2026-02-09 15:06:00', NULL, NULL, NULL, 3),
(30, 9,  '2026-02-10', '10:00:00', '11:00:00', 'checked_in', '2026-02-07 11:00:00', '2026-02-10 10:03:00', NULL, NULL, NULL, 3),
(31, 6,  '2026-02-11', '13:00:00', '14:00:00', 'checked_in', '2026-02-08 10:00:00', '2026-02-11 13:08:00', NULL, NULL, NULL, 3),
(32, 16, '2026-02-12', '08:00:00', '09:00:00', 'checked_in', '2026-02-09 09:00:00', '2026-02-12 08:05:00', NULL, NULL, NULL, 3),
# Checked-in reservations March 2026
(33, 10, '2026-03-02', '16:00:00', '17:00:00', 'checked_in', '2026-02-27 14:00:00', '2026-03-02 16:04:00', NULL, NULL, NULL, 3),
(34, 3,  '2026-03-03', '09:00:00', '10:30:00', 'checked_in', '2026-02-28 10:00:00', '2026-03-03 09:11:00', NULL, NULL, NULL, 3),
(35, 7,  '2026-03-04', '11:00:00', '12:00:00', 'checked_in', '2026-03-01 09:00:00', '2026-03-04 11:07:00', NULL, NULL, NULL, 3),
(9,  11, '2026-03-05', '14:00:00', '16:00:00', 'checked_in', '2026-03-02 11:00:00', '2026-03-05 14:06:00', NULL, NULL, NULL, 3),
(10, 4,  '2026-03-09', '10:00:00', '11:00:00', 'checked_in', '2026-03-06 09:00:00', '2026-03-09 10:03:00', NULL, NULL, NULL, 3),
(11, 1,  '2026-03-10', '13:00:00', '14:30:00', 'checked_in', '2026-03-07 08:30:00', '2026-03-10 13:09:00', NULL, NULL, NULL, 3),
# No-show reservations - suspended students (52,53,54) and minor violation students (32-35)
(52, 8,  '2026-01-10', '10:00:00', '11:00:00', 'no_show', '2026-01-07 11:00:00', '2026-01-11 08:00:00', NULL, NULL, NULL, 3),
(53, 3,  '2026-01-17', '14:00:00', '15:00:00', 'no_show', '2026-01-14 09:00:00', '2026-01-18 08:00:00', NULL, NULL, NULL, 3),
(54, 5,  '2026-01-24', '09:00:00', '10:00:00', 'no_show', '2026-01-21 10:00:00', '2026-01-25 08:00:00', NULL, NULL, NULL, 3),
(32, 9,  '2026-01-26', '11:00:00', '12:00:00', 'no_show', '2026-01-23 14:00:00', '2026-01-27 08:00:00', NULL, NULL, NULL, 3),
(33, 2,  '2026-01-27', '15:00:00', '16:00:00', 'no_show', '2026-01-24 09:30:00', '2026-01-28 08:00:00', NULL, NULL, NULL, 3),
(34, 6,  '2026-01-28', '13:00:00', '14:00:00', 'no_show', '2026-01-25 11:00:00', '2026-01-29 08:00:00', NULL, NULL, NULL, 3),
(35, 12, '2026-01-29', '16:00:00', '17:00:00', 'no_show', '2026-01-26 10:00:00', '2026-01-30 08:00:00', NULL, NULL, NULL, 3),
(52, 13, '2026-02-16', '10:00:00', '11:00:00', 'no_show', '2026-02-13 11:00:00', '2026-02-17 08:00:00', NULL, NULL, NULL, 3),
(53, 7,  '2026-02-17', '14:00:00', '15:00:00', 'no_show', '2026-02-14 09:00:00', '2026-02-18 08:00:00', NULL, NULL, NULL, 3),
(54, 1,  '2026-02-18', '09:00:00', '10:30:00', 'no_show', '2026-02-15 10:00:00', '2026-02-19 08:00:00', NULL, NULL, NULL, 3),
(52, 14, '2026-02-23', '11:00:00', '12:00:00', 'no_show', '2026-02-20 13:00:00', '2026-02-24 08:00:00', NULL, NULL, NULL, 3),
(53, 4,  '2026-02-24', '15:00:00', '16:00:00', 'no_show', '2026-02-21 09:00:00', '2026-02-25 08:00:00', NULL, NULL, NULL, 3),
(54, 15, '2026-02-25', '08:00:00', '09:00:00', 'no_show', '2026-02-22 11:00:00', '2026-02-26 08:00:00', NULL, NULL, NULL, 3),
(32, 8,  '2026-03-11', '10:00:00', '11:00:00', 'no_show', '2026-03-08 14:00:00', '2026-03-12 08:00:00', NULL, NULL, NULL, 3),
(33, 5,  '2026-03-12', '13:00:00', '14:00:00', 'no_show', '2026-03-09 09:30:00', '2026-03-13 08:00:00', NULL, NULL, NULL, 3),
(34, 9,  '2026-03-13', '16:00:00', '17:00:00', 'no_show', '2026-03-10 11:00:00', '2026-03-14 08:00:00', NULL, NULL, NULL, 3),
(35, 6,  '2026-03-16', '09:00:00', '10:00:00', 'no_show', '2026-03-13 10:00:00', '2026-03-17 08:00:00', NULL, NULL, NULL, 3),
# Cancelled reservations - late cancellations within cutoff period
(12, 16, '2026-01-12', '11:00:00', '12:00:00', 'cancelled', '2026-01-09 10:00:00', '2026-01-12 10:42:00', '2026-01-12 10:42:00', 12, 'Late cancellation - schedule conflict',     3),
(14, 17, '2026-01-19', '14:00:00', '15:00:00', 'cancelled', '2026-01-16 11:00:00', '2026-01-19 13:38:00', '2026-01-19 13:38:00', 14, 'Late cancellation - class ran over',        3),
(16, 7,  '2026-01-26', '09:00:00', '10:00:00', 'cancelled', '2026-01-23 09:00:00', '2026-01-26 08:45:00', '2026-01-26 08:45:00', 16, 'Late cancellation - transportation issue',  3),
(17, 3,  '2026-02-02', '15:00:00', '16:00:00', 'cancelled', '2026-01-30 14:00:00', '2026-02-02 14:35:00', '2026-02-02 14:35:00', 17, 'Late cancellation - study group disbanded', 3),
(18, 10, '2026-02-09', '10:00:00', '11:00:00', 'cancelled', '2026-02-06 10:00:00', '2026-02-09 09:48:00', '2026-02-09 09:48:00', 18, 'Late cancellation - illness',               3),
(19, 4,  '2026-02-16', '13:00:00', '14:00:00', 'cancelled', '2026-02-13 12:00:00', '2026-02-16 12:40:00', '2026-02-16 12:40:00', 19, 'Late cancellation - schedule conflict',     3),
(20, 11, '2026-02-23', '11:00:00', '12:00:00', 'cancelled', '2026-02-20 11:00:00', '2026-02-23 10:42:00', '2026-02-23 10:42:00', 20, 'Late cancellation - exam rescheduled',      3),
(21, 5,  '2026-03-02', '14:00:00', '15:00:00', 'cancelled', '2026-02-27 13:00:00', '2026-03-02 13:35:00', '2026-03-02 13:35:00', 21, 'Late cancellation - transportation issue',  3),
(22, 13, '2026-03-09', '09:00:00', '10:00:00', 'cancelled', '2026-03-06 09:00:00', '2026-03-09 08:45:00', '2026-03-09 08:45:00', 22, 'Late cancellation - class ran over',        3),
(23, 2,  '2026-03-16', '15:00:00', '16:00:00', 'cancelled', '2026-03-13 14:00:00', '2026-03-16 14:38:00', '2026-03-16 14:38:00', 23, 'Late cancellation - schedule conflict',     3),
(24, 8,  '2026-03-23', '11:00:00', '12:00:00', 'cancelled', '2026-03-20 11:00:00', '2026-03-23 10:42:00', '2026-03-23 10:42:00', 24, 'Late cancellation - study group cancelled', 3),
(25, 14, '2026-03-30', '14:00:00', '15:00:00', 'cancelled', '2026-03-27 10:00:00', '2026-03-30 13:35:00', '2026-03-30 13:35:00', 25, 'Late cancellation - illness',               3),
(26, 6,  '2026-04-06', '10:00:00', '11:00:00', 'cancelled', '2026-04-03 09:00:00', '2026-04-06 09:48:00', '2026-04-06 09:48:00', 26, 'Late cancellation - transportation issue',  3),
(27, 15, '2026-04-13', '13:00:00', '14:00:00', 'cancelled', '2026-04-10 12:00:00', '2026-04-13 12:40:00', '2026-04-13 12:40:00', 27, 'Late cancellation - exam conflict',         3),
(28, 3,  '2026-04-20', '15:00:00', '16:00:00', 'cancelled', '2026-04-17 14:00:00', '2026-04-20 14:42:00', '2026-04-20 14:42:00', 28, 'Late cancellation - schedule conflict',     3),
# Upcoming reserved bookings
(29, 7,  '2026-04-20', '10:00:00', '11:00:00', 'reserved', '2026-04-14 11:00:00', '2026-04-14 11:00:00', NULL, NULL, NULL, 3),
(30, 3,  '2026-04-21', '14:00:00', '15:30:00', 'reserved', '2026-04-14 09:30:00', '2026-04-14 09:30:00', NULL, NULL, NULL, 3),
(31, 1,  '2026-04-22', '09:00:00', '11:00:00', 'reserved', '2026-04-14 10:00:00', '2026-04-14 10:00:00', NULL, NULL, NULL, 3);


# Insert check-in records for all checked_in reservations
# reservation_id 1-30 correspond to the checked_in reservations above
# Check-in times fall within the 15-minute grace period from reservation start
# Three records use admin_override where staff manually recorded student arrival

INSERT INTO Check_Ins (reservation_id, user_id, checkin_time, method, recorded_by_user_id, created_at)
VALUES
(1,  9,  '2026-01-05 09:07:00', 'student_ui',    NULL, '2026-01-05 09:07:00'),
(2,  10, '2026-01-06 10:05:00', 'student_ui',    NULL, '2026-01-06 10:05:00'),
(3,  11, '2026-01-07 14:10:00', 'student_ui',    NULL, '2026-01-07 14:10:00'),
(4,  12, '2026-01-08 11:03:00', 'student_ui',    NULL, '2026-01-08 11:03:00'),
(5,  13, '2026-01-09 13:08:00', 'student_ui',    NULL, '2026-01-09 13:08:00'),
(6,  14, '2026-01-12 15:12:00', 'student_ui',    NULL, '2026-01-12 15:12:00'),
(7,  15, '2026-01-13 08:06:00', 'student_ui',    NULL, '2026-01-13 08:06:00'),
(8,  16, '2026-01-14 16:04:00', 'student_ui',    NULL, '2026-01-14 16:04:00'),
(9,  17, '2026-01-15 09:09:00', 'student_ui',    NULL, '2026-01-15 09:09:00'),
(10, 18, '2026-01-16 10:07:00', 'admin_override', 1,   '2026-01-16 10:07:00'),
(11, 19, '2026-01-19 13:05:00', 'student_ui',    NULL, '2026-01-19 13:05:00'),
(12, 20, '2026-01-20 11:11:00', 'student_ui',    NULL, '2026-01-20 11:11:00'),
(13, 21, '2026-01-21 14:06:00', 'student_ui',    NULL, '2026-01-21 14:06:00'),
(14, 22, '2026-01-22 09:03:00', 'student_ui',    NULL, '2026-01-22 09:03:00'),
(15, 23, '2026-01-23 16:08:00', 'student_ui',    NULL, '2026-01-23 16:08:00'),
(16, 24, '2026-02-02 10:04:00', 'student_ui',    NULL, '2026-02-02 10:04:00'),
(17, 25, '2026-02-03 13:10:00', 'admin_override', 2,   '2026-02-03 13:10:00'),
(18, 26, '2026-02-04 09:07:00', 'student_ui',    NULL, '2026-02-04 09:07:00'),
(19, 27, '2026-02-05 14:05:00', 'student_ui',    NULL, '2026-02-05 14:05:00'),
(20, 28, '2026-02-06 11:09:00', 'student_ui',    NULL, '2026-02-06 11:09:00'),
(21, 29, '2026-02-09 15:06:00', 'student_ui',    NULL, '2026-02-09 15:06:00'),
(22, 30, '2026-02-10 10:03:00', 'student_ui',    NULL, '2026-02-10 10:03:00'),
(23, 31, '2026-02-11 13:08:00', 'student_ui',    NULL, '2026-02-11 13:08:00'),
(24, 32, '2026-02-12 08:05:00', 'student_ui',    NULL, '2026-02-12 08:05:00'),
(25, 33, '2026-03-02 16:04:00', 'student_ui',    NULL, '2026-03-02 16:04:00'),
(26, 34, '2026-03-03 09:11:00', 'student_ui',    NULL, '2026-03-03 09:11:00'),
(27, 35, '2026-03-04 11:07:00', 'admin_override', 3,   '2026-03-04 11:07:00'),
(28, 9,  '2026-03-05 14:06:00', 'student_ui',    NULL, '2026-03-05 14:06:00'),
(29, 10, '2026-03-09 10:03:00', 'student_ui',    NULL, '2026-03-09 10:03:00'),
(30, 11, '2026-03-10 13:09:00', 'student_ui',    NULL, '2026-03-10 13:09:00');


# Insert violation records
# reservation_id 31-47 : no_show violations  (3 penalty points each)
# reservation_id 48-62 : late_cancel violations (2 penalty points each)
# Violations for suspended students (52,53,54) are all active
# Some violations for minor-penalty students are resolved by library staff

INSERT INTO Violations (user_id, reservation_id, violation_type, points_assessed, status, notes, created_at, resolved_at, resolved_by_user_id)
VALUES
# No-show violations
(52, 31, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                   '2026-01-10 11:30:00', NULL,                  NULL),
(53, 32, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                   '2026-01-17 15:30:00', NULL,                  NULL),
(54, 33, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                   '2026-01-24 10:30:00', NULL,                  NULL),
(32, 34, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                   '2026-01-26 12:30:00', '2026-02-02 10:00:00', 1),
(33, 35, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                   '2026-01-27 16:30:00', '2026-02-03 10:00:00', 2),
(34, 36, 'no_show', 3, 'resolved', 'Student failed to appear for reserved time slot',                              '2026-01-28 14:30:00', '2026-02-04 10:00:00', 3),
(35, 37, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                   '2026-01-29 17:30:00', '2026-02-05 10:00:00', 1),
(52, 38, 'no_show', 3, 'active',   'Second no-show occurrence; student did not check in within grace period',      '2026-02-16 11:30:00', NULL,                  NULL),
(53, 39, 'no_show', 3, 'active',   'Second no-show occurrence; student did not check in within grace period',      '2026-02-17 15:30:00', NULL,                  NULL),
(54, 40, 'no_show', 3, 'active',   'Second no-show occurrence; student did not check in within grace period',      '2026-02-18 11:00:00', NULL,                  NULL),
(52, 41, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',              '2026-02-23 12:30:00', NULL,                  NULL),
(53, 42, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',              '2026-02-24 16:30:00', NULL,                  NULL),
(54, 43, 'no_show', 3, 'active',   'Third no-show occurrence; account flagged for suspension review',              '2026-02-25 09:30:00', NULL,                  NULL),
(32, 44, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                   '2026-03-11 11:30:00', '2026-03-18 09:00:00', 2),
(33, 45, 'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                   '2026-03-12 14:30:00', '2026-03-19 09:00:00', 3),
(34, 46, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                   '2026-03-13 17:30:00', NULL,                  NULL),
(35, 47, 'no_show', 3, 'active',   'Student did not appear for reserved single study room',                        '2026-03-16 10:30:00', NULL,                  NULL),
# Late cancellation violations
(12, 48, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-01-12 10:42:00', '2026-01-19 10:00:00', 1),
(14, 49, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-01-19 13:38:00', '2026-01-26 10:00:00', 2),
(16, 50, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-01-26 08:45:00', '2026-02-02 10:00:00', 3),
(17, 51, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-02-02 14:35:00', NULL,                  NULL),
(18, 52, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-02-09 09:48:00', NULL,                  NULL),
(19, 53, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-02-16 12:40:00', NULL,                  NULL),
(20, 54, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-02-23 10:42:00', NULL,                  NULL),
(21, 55, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-03-02 13:35:00', NULL,                  NULL),
(22, 56, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-03-09 08:45:00', NULL,                  NULL),
(23, 57, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-03-16 14:38:00', NULL,                  NULL),
(24, 58, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-03-23 10:42:00', NULL,                  NULL),
(25, 59, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-03-30 13:35:00', NULL,                  NULL),
(26, 60, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-04-06 09:48:00', NULL,                  NULL),
(27, 61, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-04-13 12:40:00', NULL,                  NULL),
(28, 62, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period',   '2026-04-20 14:42:00', NULL,                  NULL);


# Insert 20 additional student accounts
# user_id 55-74 (auto-incremented after existing 54 users)

INSERT INTO Users (first_name, last_name, email, phone_number, date_of_birth, password_hash, role, account_status, penalty_points, created_at)
VALUES
('Tyler',     'Brooks',    'brook4ty@cmich.edu',  '734-555-0201', '2003-04-11', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Natalie',   'Hughes',    'hughe2na@cmich.edu',  '616-555-0202', '2004-02-27', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Dylan',     'Sanders',   'sande6dy@cmich.edu',  '269-555-0203', '2002-11-03', SHA2('Student@123',256), 'student', 'active', 3, '2025-09-08 10:00:00'),
('Aubrey',    'Coleman',   'colem8au@cmich.edu',  '810-555-0204', '2003-07-19', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Caleb',     'Jenkins',   'jenki5ca@cmich.edu',  '947-555-0205', '2001-05-30', SHA2('Student@123',256), 'student', 'active', 6, '2025-09-08 10:00:00'),
('Savannah',  'Perry',     'perry3sa@cmich.edu',  '231-555-0206', '2004-09-14', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Hunter',    'Russell',   'russe7hu@cmich.edu',  '517-555-0207', '2002-03-08', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Leah',      'Griffin',   'griff2le@cmich.edu',  '989-555-0208', '2003-12-21', SHA2('Student@123',256), 'student', 'active', 3, '2025-09-08 10:00:00'),
('Eli',       'Diaz',      'diaz9el@cmich.edu',   '734-555-0209', '2001-08-16', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Paisley',   'Hayes',     'hayes1pa@cmich.edu',  '616-555-0210', '2004-06-05', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Connor',    'Myers',     'myers3co@cmich.edu',  '248-555-0211', '2002-01-25', SHA2('Student@123',256), 'student', 'active', 6, '2025-09-08 10:00:00'),
('Violet',    'Ford',      'ford7vi@cmich.edu',   '517-555-0212', '2003-10-09', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Brayden',   'Hamilton',  'hamil4br@cmich.edu',  '269-555-0213', '2001-04-22', SHA2('Student@123',256), 'student', 'active', 3, '2025-09-08 10:00:00'),
('Aurora',    'Graham',    'graha6au@cmich.edu',  '810-555-0214', '2004-11-07', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Colton',    'Sullivan',  'sulli9co@cmich.edu',  '947-555-0215', '2002-07-13', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Naomi',     'Ward',      'ward5na@cmich.edu',   '231-555-0216', '2003-03-28', SHA2('Student@123',256), 'student', 'active', 6, '2025-09-08 10:00:00'),
('Jaxon',     'Torres',    'torre2ja@cmich.edu',  '734-555-0217', '2001-09-17', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Delilah',   'Ramirez',   'ramire8de@cmich.edu', '616-555-0218', '2004-01-04', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00'),
('Easton',    'James',     'james3ea@cmich.edu',  '989-555-0219', '2002-06-20', SHA2('Student@123',256), 'student', 'active', 3, '2025-09-08 10:00:00'),
('Ivy',       'Watson',    'watso1iv@cmich.edu',  '248-555-0220', '2003-08-31', SHA2('Student@123',256), 'student', 'active', 0, '2025-09-08 10:00:00');


# Insert 35 additional reservations
# Spread across January to April 2026
# Mix of checked_in, no_show, cancelled and reserved statuses
# Uses user_ids 55-74 (new students) and some existing students
# Uses room_ids 1-17 (all real project rooms)
# rule_set_id = 3 (active rule set)
#
# reservation_id 66-95  : checked_in (30 records - supports 30 check-ins)
# reservation_id 96-105 : no_show    (10 records - supports 10 violations)
# reservation_id 106-115: cancelled  (10 records - supports 10 violations)
# reservation_id 116-120: reserved   (5 upcoming records)
# Total new: 55 reservations (66-120)

INSERT INTO Reservations (user_id, room_id, reservation_date, start_time, end_time, status, created_at, updated_at, canceled_at, canceled_by_user_id, reason, rule_set_id)
VALUES
# Checked-in reservations using new students (user_id 55-74)
(55, 3,  '2026-01-08', '09:00:00', '10:00:00', 'checked_in', '2026-01-05 10:00:00', '2026-01-08 09:08:00', NULL, NULL, NULL, 3),
(56, 7,  '2026-01-09', '11:00:00', '12:00:00', 'checked_in', '2026-01-06 11:00:00', '2026-01-09 11:06:00', NULL, NULL, NULL, 3),
(57, 1,  '2026-01-10', '14:00:00', '16:00:00', 'checked_in', '2026-01-07 09:00:00', '2026-01-10 14:11:00', NULL, NULL, NULL, 3),
(58, 4,  '2026-01-13', '10:00:00', '11:00:00', 'checked_in', '2026-01-10 10:00:00', '2026-01-13 10:04:00', NULL, NULL, NULL, 3),
(59, 8,  '2026-01-14', '13:00:00', '14:00:00', 'checked_in', '2026-01-11 08:00:00', '2026-01-14 13:09:00', NULL, NULL, NULL, 3),
(60, 5,  '2026-01-15', '15:00:00', '17:00:00', 'checked_in', '2026-01-12 14:00:00', '2026-01-15 15:07:00', NULL, NULL, NULL, 3),
(61, 9,  '2026-01-16', '08:00:00', '09:00:00', 'checked_in', '2026-01-13 11:00:00', '2026-01-16 08:05:00', NULL, NULL, NULL, 3),
(62, 2,  '2026-01-20', '10:00:00', '12:00:00', 'checked_in', '2026-01-17 10:00:00', '2026-01-20 10:03:00', NULL, NULL, NULL, 3),
(63, 10, '2026-01-21', '14:00:00', '15:00:00', 'checked_in', '2026-01-18 09:00:00', '2026-01-21 14:08:00', NULL, NULL, NULL, 3),
(64, 6,  '2026-01-22', '16:00:00', '17:00:00', 'checked_in', '2026-01-19 13:00:00', '2026-01-22 16:06:00', NULL, NULL, NULL, 3),
(65, 11, '2026-02-03', '09:00:00', '10:00:00', 'checked_in', '2026-01-31 09:00:00', '2026-02-03 09:10:00', NULL, NULL, NULL, 3),
(66, 3,  '2026-02-04', '11:00:00', '12:30:00', 'checked_in', '2026-02-01 10:00:00', '2026-02-04 11:05:00', NULL, NULL, NULL, 3),
(67, 7,  '2026-02-05', '13:00:00', '14:00:00', 'checked_in', '2026-02-02 08:00:00', '2026-02-05 13:07:00', NULL, NULL, NULL, 3),
(68, 1,  '2026-02-10', '15:00:00', '17:00:00', 'checked_in', '2026-02-07 11:00:00', '2026-02-10 15:04:00', NULL, NULL, NULL, 3),
(69, 4,  '2026-02-11', '08:00:00', '09:00:00', 'checked_in', '2026-02-08 09:00:00', '2026-02-11 08:09:00', NULL, NULL, NULL, 3),
(70, 13, '2026-02-12', '10:00:00', '11:00:00', 'checked_in', '2026-02-09 10:00:00', '2026-02-12 10:06:00', NULL, NULL, NULL, 3),
(71, 5,  '2026-02-17', '13:00:00', '15:00:00', 'checked_in', '2026-02-14 13:00:00', '2026-02-17 13:08:00', NULL, NULL, NULL, 3),
(72, 8,  '2026-02-18', '16:00:00', '17:00:00', 'checked_in', '2026-02-15 14:00:00', '2026-02-18 16:05:00', NULL, NULL, NULL, 3),
(73, 2,  '2026-02-19', '09:00:00', '10:30:00', 'checked_in', '2026-02-16 09:00:00', '2026-02-19 09:03:00', NULL, NULL, NULL, 3),
(74, 14, '2026-02-20', '11:00:00', '12:00:00', 'checked_in', '2026-02-17 10:00:00', '2026-02-20 11:11:00', NULL, NULL, NULL, 3),
(55, 6,  '2026-03-03', '14:00:00', '15:00:00', 'checked_in', '2026-02-28 11:00:00', '2026-03-03 14:06:00', NULL, NULL, NULL, 3),
(56, 9,  '2026-03-04', '16:00:00', '17:00:00', 'checked_in', '2026-03-01 14:00:00', '2026-03-04 16:04:00', NULL, NULL, NULL, 3),
(57, 3,  '2026-03-05', '09:00:00', '10:00:00', 'checked_in', '2026-03-02 09:00:00', '2026-03-05 09:09:00', NULL, NULL, NULL, 3),
(58, 15, '2026-03-10', '11:00:00', '12:30:00', 'checked_in', '2026-03-07 10:00:00', '2026-03-10 11:07:00', NULL, NULL, NULL, 3),
(59, 1,  '2026-03-11', '13:00:00', '14:00:00', 'checked_in', '2026-03-08 08:00:00', '2026-03-11 13:05:00', NULL, NULL, NULL, 3),
(60, 4,  '2026-03-17', '15:00:00', '17:00:00', 'checked_in', '2026-03-14 13:00:00', '2026-03-17 15:08:00', NULL, NULL, NULL, 3),
(61, 10, '2026-03-18', '08:00:00', '09:00:00', 'checked_in', '2026-03-15 09:00:00', '2026-03-18 08:04:00', NULL, NULL, NULL, 3),
(62, 7,  '2026-03-24', '10:00:00', '11:00:00', 'checked_in', '2026-03-21 10:00:00', '2026-03-24 10:06:00', NULL, NULL, NULL, 3),
(63, 5,  '2026-03-25', '13:00:00', '14:30:00', 'checked_in', '2026-03-22 11:00:00', '2026-03-25 13:03:00', NULL, NULL, NULL, 3),
(64, 16, '2026-03-26', '15:00:00', '16:00:00', 'checked_in', '2026-03-23 14:00:00', '2026-03-26 15:09:00', NULL, NULL, NULL, 3),
# No-show reservations
(65, 2,  '2026-01-17', '09:00:00', '10:00:00', 'no_show', '2026-01-14 10:00:00', '2026-01-18 08:00:00', NULL, NULL, NULL, 3),
(66, 6,  '2026-01-31', '11:00:00', '12:00:00', 'no_show', '2026-01-28 11:00:00', '2026-02-01 08:00:00', NULL, NULL, NULL, 3),
(67, 12, '2026-02-14', '14:00:00', '15:00:00', 'no_show', '2026-02-11 09:00:00', '2026-02-15 08:00:00', NULL, NULL, NULL, 3),
(68, 3,  '2026-02-28', '09:00:00', '10:00:00', 'no_show', '2026-02-25 10:00:00', '2026-03-01 08:00:00', NULL, NULL, NULL, 3),
(69, 8,  '2026-03-07', '13:00:00', '14:00:00', 'no_show', '2026-03-04 13:00:00', '2026-03-08 08:00:00', NULL, NULL, NULL, 3),
(70, 1,  '2026-03-14', '15:00:00', '16:00:00', 'no_show', '2026-03-11 14:00:00', '2026-03-15 08:00:00', NULL, NULL, NULL, 3),
(71, 4,  '2026-03-20', '10:00:00', '11:00:00', 'no_show', '2026-03-17 10:00:00', '2026-03-21 08:00:00', NULL, NULL, NULL, 3),
(72, 9,  '2026-03-27', '08:00:00', '09:00:00', 'no_show', '2026-03-24 09:00:00', '2026-03-28 08:00:00', NULL, NULL, NULL, 3),
(73, 5,  '2026-04-03', '16:00:00', '17:00:00', 'no_show', '2026-03-31 14:00:00', '2026-04-04 08:00:00', NULL, NULL, NULL, 3),
(74, 11, '2026-04-07', '11:00:00', '12:00:00', 'no_show', '2026-04-04 11:00:00', '2026-04-08 08:00:00', NULL, NULL, NULL, 3),
# Cancelled reservations
(55, 17, '2026-01-20', '09:00:00', '10:00:00', 'cancelled', '2026-01-17 09:00:00', '2026-01-20 08:42:00', '2026-01-20 08:42:00', 55, 'Late cancellation - schedule conflict',     3),
(56, 3,  '2026-02-03', '13:00:00', '14:00:00', 'cancelled', '2026-01-31 13:00:00', '2026-02-03 12:38:00', '2026-02-03 12:38:00', 56, 'Late cancellation - illness',               3),
(57, 7,  '2026-02-10', '15:00:00', '16:00:00', 'cancelled', '2026-02-07 14:00:00', '2026-02-10 14:45:00', '2026-02-10 14:45:00', 57, 'Late cancellation - class ran over',        3),
(58, 1,  '2026-02-17', '09:00:00', '10:00:00', 'cancelled', '2026-02-14 09:00:00', '2026-02-17 08:40:00', '2026-02-17 08:40:00', 58, 'Late cancellation - transportation issue',  3),
(59, 4,  '2026-02-24', '11:00:00', '12:00:00', 'cancelled', '2026-02-21 11:00:00', '2026-02-24 10:42:00', '2026-02-24 10:42:00', 59, 'Late cancellation - exam rescheduled',      3),
(60, 2,  '2026-03-03', '14:00:00', '15:00:00', 'cancelled', '2026-02-28 13:00:00', '2026-03-03 13:35:00', '2026-03-03 13:35:00', 60, 'Late cancellation - study group disbanded', 3),
(61, 8,  '2026-03-10', '16:00:00', '17:00:00', 'cancelled', '2026-03-07 15:00:00', '2026-03-10 15:48:00', '2026-03-10 15:48:00', 61, 'Late cancellation - schedule conflict',     3),
(62, 5,  '2026-03-17', '09:00:00', '10:00:00', 'cancelled', '2026-03-14 09:00:00', '2026-03-17 08:44:00', '2026-03-17 08:44:00', 62, 'Late cancellation - class ran over',        3),
(63, 6,  '2026-03-24', '11:00:00', '12:30:00', 'cancelled', '2026-03-21 10:00:00', '2026-03-24 10:38:00', '2026-03-24 10:38:00', 63, 'Late cancellation - transportation issue',  3),
(64, 13, '2026-03-31', '14:00:00', '15:00:00', 'cancelled', '2026-03-28 13:00:00', '2026-03-31 13:42:00', '2026-03-31 13:42:00', 64, 'Late cancellation - illness',               3),
# Upcoming reserved bookings
(65, 3,  '2026-04-18', '09:00:00', '10:00:00', 'reserved', '2026-04-14 09:00:00', '2026-04-14 09:00:00', NULL, NULL, NULL, 3),
(66, 7,  '2026-04-18', '11:00:00', '12:00:00', 'reserved', '2026-04-14 10:00:00', '2026-04-14 10:00:00', NULL, NULL, NULL, 3),
(67, 1,  '2026-04-19', '14:00:00', '16:00:00', 'reserved', '2026-04-14 11:00:00', '2026-04-14 11:00:00', NULL, NULL, NULL, 3),
(68, 5,  '2026-04-21', '10:00:00', '11:00:00', 'reserved', '2026-04-14 12:00:00', '2026-04-14 12:00:00', NULL, NULL, NULL, 3),
(69, 4,  '2026-04-22', '13:00:00', '14:30:00', 'reserved', '2026-04-14 13:00:00', '2026-04-14 13:00:00', NULL, NULL, NULL, 3);


# Insert check-in records for the 30 new checked_in reservations above
# reservation_id 66-95 correspond to the checked_in reservations inserted above
# Check-in times fall within the 15-minute grace period

INSERT INTO Check_Ins (reservation_id, user_id, checkin_time, method, recorded_by_user_id, created_at)
VALUES
(66, 55, '2026-01-08 09:08:00', 'student_ui',    NULL, '2026-01-08 09:08:00'),
(67, 56, '2026-01-09 11:06:00', 'student_ui',    NULL, '2026-01-09 11:06:00'),
(68, 57, '2026-01-10 14:11:00', 'student_ui',    NULL, '2026-01-10 14:11:00'),
(69, 58, '2026-01-13 10:04:00', 'student_ui',    NULL, '2026-01-13 10:04:00'),
(70, 59, '2026-01-14 13:09:00', 'student_ui',    NULL, '2026-01-14 13:09:00'),
(71, 60, '2026-01-15 15:07:00', 'student_ui',    NULL, '2026-01-15 15:07:00'),
(72, 61, '2026-01-16 08:05:00', 'student_ui',    NULL, '2026-01-16 08:05:00'),
(73, 62, '2026-01-20 10:03:00', 'admin_override', 4,   '2026-01-20 10:03:00'),
(74, 63, '2026-01-21 14:08:00', 'student_ui',    NULL, '2026-01-21 14:08:00'),
(75, 64, '2026-01-22 16:06:00', 'student_ui',    NULL, '2026-01-22 16:06:00'),
(76, 65, '2026-02-03 09:10:00', 'student_ui',    NULL, '2026-02-03 09:10:00'),
(77, 66, '2026-02-04 11:05:00', 'student_ui',    NULL, '2026-02-04 11:05:00'),
(78, 67, '2026-02-05 13:07:00', 'student_ui',    NULL, '2026-02-05 13:07:00'),
(79, 68, '2026-02-10 15:04:00', 'student_ui',    NULL, '2026-02-10 15:04:00'),
(80, 69, '2026-02-11 08:09:00', 'student_ui',    NULL, '2026-02-11 08:09:00'),
(81, 70, '2026-02-12 10:06:00', 'admin_override', 5,   '2026-02-12 10:06:00'),
(82, 71, '2026-02-17 13:08:00', 'student_ui',    NULL, '2026-02-17 13:08:00'),
(83, 72, '2026-02-18 16:05:00', 'student_ui',    NULL, '2026-02-18 16:05:00'),
(84, 73, '2026-02-19 09:03:00', 'student_ui',    NULL, '2026-02-19 09:03:00'),
(85, 74, '2026-02-20 11:11:00', 'student_ui',    NULL, '2026-02-20 11:11:00'),
(86, 55, '2026-03-03 14:06:00', 'student_ui',    NULL, '2026-03-03 14:06:00'),
(87, 56, '2026-03-04 16:04:00', 'student_ui',    NULL, '2026-03-04 16:04:00'),
(88, 57, '2026-03-05 09:09:00', 'student_ui',    NULL, '2026-03-05 09:09:00'),
(89, 58, '2026-03-10 11:07:00', 'admin_override', 6,   '2026-03-10 11:07:00'),
(90, 59, '2026-03-11 13:05:00', 'student_ui',    NULL, '2026-03-11 13:05:00'),
(91, 60, '2026-03-17 15:08:00', 'student_ui',    NULL, '2026-03-17 15:08:00'),
(92, 61, '2026-03-18 08:04:00', 'student_ui',    NULL, '2026-03-18 08:04:00'),
(93, 62, '2026-03-24 10:06:00', 'student_ui',    NULL, '2026-03-24 10:06:00'),
(94, 63, '2026-03-25 13:03:00', 'student_ui',    NULL, '2026-03-25 13:03:00'),
(95, 64, '2026-03-26 15:09:00', 'student_ui',    NULL, '2026-03-26 15:09:00');


# Insert violations for new no_show reservations (reservation_id 96-105)
# and new cancelled reservations (reservation_id 106-115)
# No-show: 3 points each
# Late cancel: 2 points each

INSERT INTO Violations (user_id, reservation_id, violation_type, points_assessed, status, notes, created_at, resolved_at, resolved_by_user_id)
VALUES
# No-show violations
(65, 96,  'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-01-17 10:30:00', NULL,                  NULL),
(66, 97,  'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-01-31 12:30:00', NULL,                  NULL),
(67, 98,  'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                 '2026-02-14 15:30:00', '2026-02-21 10:00:00', 1),
(68, 99,  'no_show', 3, 'resolved', 'Student did not check in within the 15-minute grace period',                 '2026-02-28 10:30:00', '2026-03-07 10:00:00', 2),
(69, 100, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-03-07 14:30:00', NULL,                  NULL),
(70, 101, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-03-14 16:30:00', NULL,                  NULL),
(71, 102, 'no_show', 3, 'resolved', 'Student failed to appear for reserved time slot',                            '2026-03-20 11:30:00', '2026-03-27 10:00:00', 3),
(72, 103, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-03-27 09:30:00', NULL,                  NULL),
(73, 104, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-04-03 17:30:00', NULL,                  NULL),
(74, 105, 'no_show', 3, 'active',   'Student did not check in within the 15-minute grace period',                 '2026-04-07 12:30:00', NULL,                  NULL),
# Late cancellation violations
(55, 106, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-01-20 08:42:00', '2026-01-27 10:00:00', 1),
(56, 107, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-03 12:38:00', NULL,                  NULL),
(57, 108, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-10 14:45:00', NULL,                  NULL),
(58, 109, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-17 08:40:00', '2026-02-24 10:00:00', 2),
(59, 110, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-02-24 10:42:00', NULL,                  NULL),
(60, 111, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-03 13:35:00', NULL,                  NULL),
(61, 112, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-10 15:48:00', NULL,                  NULL),
(62, 113, 'late_cancel', 2, 'resolved', 'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-17 08:44:00', '2026-03-24 10:00:00', 3),
(63, 114, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-24 10:38:00', NULL,                  NULL),
(64, 115, 'late_cancel', 2, 'active',   'Reservation cancelled within the 30-minute cancellation cutoff period', '2026-03-31 13:42:00', NULL,                  NULL);


# Mark all past checked_in reservations as completed
# This reflects real-world behavior where the system updates status after end_time passes

SET SQL_SAFE_UPDATES = 0;

UPDATE Reservations
SET status = 'completed'
WHERE status = 'checked_in'
AND reservation_id IN (SELECT reservation_id FROM Check_Ins)
AND CONCAT(reservation_date, ' ', end_time) < NOW();

SET SQL_SAFE_UPDATES = 1;

# Database initialisation script.
# Run once to create tables and add any columns that were added after initial deployment.
# Safe to re-run: CREATE IF NOT EXISTS and duplicate-column guards prevent data loss.
# Usage: python create_db.py

import mysql.connector
from mysql.connector import Error
import credentials

# Each statement uses IF NOT EXISTS so re-running is idempotent.
CREATE_STATEMENTS = [
    # Users: core account table; role determines which screens are accessible.
    """
    CREATE TABLE IF NOT EXISTS Users (
        user_id          INT           NOT NULL AUTO_INCREMENT,
        first_name       VARCHAR(100)  NOT NULL,
        last_name        VARCHAR(100)  NOT NULL,
        email            VARCHAR(255)  NOT NULL UNIQUE,
        phone_number     VARCHAR(20)   NULL,
        date_of_birth    DATE          NULL,
        password_hash    VARCHAR(255)  NOT NULL,
        role             ENUM('student','admin') NOT NULL DEFAULT 'student',
        account_status   ENUM('active','suspended') NOT NULL DEFAULT 'active',
        penalty_points   INT           NOT NULL DEFAULT 0,
        suspended_until  DATE          NULL,
        created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,
        last_login_at    DATETIME      NULL,
        password_reset_required TINYINT(1) NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # Rooms: physical study rooms available for reservation.
    """
    CREATE TABLE IF NOT EXISTS Rooms (
        room_id          INT           NOT NULL AUTO_INCREMENT,
        room_code        VARCHAR(50)   NULL,
        room_name        VARCHAR(100)  NULL,
        room_category    VARCHAR(50)   NOT NULL,
        floor_number     INT           NULL,
        room_number      VARCHAR(20)   NOT NULL,
        capacity         INT           NOT NULL,
        status           ENUM('available','blocked') NOT NULL DEFAULT 'available',
        description      TEXT          NULL,
        PRIMARY KEY (room_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # Rules: configurable policy parameters (grace period, penalty points, suspension thresholds).
    # Only the most recent active rule set is enforced by the no-show checker.
    """
    CREATE TABLE IF NOT EXISTS Rules (
        rule_set_id                INT     NOT NULL AUTO_INCREMENT,
        is_active                  BOOLEAN NOT NULL DEFAULT TRUE,
        effective_from             DATE    NOT NULL,
        max_booking_minutes        INT     NOT NULL DEFAULT 120,
        checkin_grace_minutes      INT     NOT NULL DEFAULT 15,
        cooldown_minutes           INT     NOT NULL DEFAULT 0,
        cancel_cutoff_minutes      INT     NOT NULL DEFAULT 60,
        points_no_show             INT     NOT NULL DEFAULT 10,
        points_late_cancel         INT     NOT NULL DEFAULT 5,
        suspension_threshold_points INT   NOT NULL DEFAULT 30,
        suspension_duration_days   INT     NOT NULL DEFAULT 14,
        created_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (rule_set_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # Reservations: each row is a single room booking by a student.
    # rule_set_id links to the active policy at time of booking.
    # FK ON DELETE CASCADE removes reservations when a user or room is deleted.
    """
    CREATE TABLE IF NOT EXISTS Reservations (
        reservation_id      INT      NOT NULL AUTO_INCREMENT,
        user_id             INT      NOT NULL,
        room_id             INT      NOT NULL,
        reservation_date    DATE     NOT NULL,
        start_time          TIME     NOT NULL,
        end_time            TIME     NOT NULL,
        status              ENUM('pending','confirmed','checked_in',
                                 'cancelled','no_show') NOT NULL DEFAULT 'pending',
        created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
        canceled_at         DATETIME NULL,
        canceled_by_user_id INT      NULL,
        reason              TEXT     NULL,
        rule_set_id         INT      NULL,
        PRIMARY KEY (reservation_id),
        FOREIGN KEY (user_id) REFERENCES Users(user_id)    ON DELETE CASCADE,
        FOREIGN KEY (room_id) REFERENCES Rooms(room_id)    ON DELETE CASCADE,
        FOREIGN KEY (rule_set_id) REFERENCES Rules(rule_set_id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # Check_Ins: records the timestamp when a student physically checked in.
    # A reservation without a Check_Ins row past the grace period becomes a no-show.
    """
    CREATE TABLE IF NOT EXISTS Check_Ins (
        checkin_id          INT      NOT NULL AUTO_INCREMENT,
        reservation_id      INT      NOT NULL,
        user_id             INT      NOT NULL,
        checkin_time        DATETIME NOT NULL,
        method              VARCHAR(50) NULL,
        recorded_by_user_id INT      NULL,
        created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (checkin_id),
        FOREIGN KEY (reservation_id) REFERENCES Reservations(reservation_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id)        REFERENCES Users(user_id)               ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # Violations: penalty events triggered by no-shows or late cancellations.
    # points_assessed is copied from Rules at the time of the event, not recalculated.
    """
    CREATE TABLE IF NOT EXISTS Violations (
        violation_id        INT      NOT NULL AUTO_INCREMENT,
        user_id             INT      NOT NULL,
        reservation_id      INT      NOT NULL,
        violation_type      ENUM('no_show','late_cancel') NOT NULL,
        points_assessed     INT      NOT NULL DEFAULT 0,
        status              ENUM('open','resolved','appealed') NOT NULL DEFAULT 'open',
        notes               TEXT     NULL,
        created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at         DATETIME NULL,
        resolved_by_user_id INT      NULL,
        PRIMARY KEY (violation_id),
        FOREIGN KEY (user_id)        REFERENCES Users(user_id)               ON DELETE CASCADE,
        FOREIGN KEY (reservation_id) REFERENCES Reservations(reservation_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

# ALTER statements add columns that were introduced after the initial schema.
# Error 1060 (duplicate column) is silently skipped so this is safe to re-run.
ALTER_STATEMENTS = [
    # Users
    ("Users", "phone_number",
     "ALTER TABLE Users ADD COLUMN phone_number VARCHAR(20) NULL AFTER email"),
    ("Users", "date_of_birth",
     "ALTER TABLE Users ADD COLUMN date_of_birth DATE NULL AFTER phone_number"),
    ("Users", "suspended_until",
     "ALTER TABLE Users ADD COLUMN suspended_until DATE NULL AFTER penalty_points"),
    ("Users", "updated_at",
     "ALTER TABLE Users ADD COLUMN updated_at DATETIME NOT NULL "
     "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at"),
    ("Users", "last_login_at",
     "ALTER TABLE Users ADD COLUMN last_login_at DATETIME NULL AFTER updated_at"),
    ("Users", "password_reset_required",
     "ALTER TABLE Users ADD COLUMN password_reset_required TINYINT(1) NOT NULL DEFAULT 0 AFTER last_login_at"),

    # Rooms
    ("Rooms", "room_code",
     "ALTER TABLE Rooms ADD COLUMN room_code VARCHAR(50) NULL AFTER room_id"),
    ("Rooms", "room_name",
     "ALTER TABLE Rooms ADD COLUMN room_name VARCHAR(100) NULL AFTER room_code"),
    ("Rooms", "floor_number",
     "ALTER TABLE Rooms ADD COLUMN floor_number INT NULL AFTER room_category"),
    ("Rooms", "description",
     "ALTER TABLE Rooms ADD COLUMN description TEXT NULL AFTER status"),

    # Rules
    ("Rules", "created_at",
     "ALTER TABLE Rules ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
    ("Rules", "updated_at",
     "ALTER TABLE Rules ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),

    # Reservations
    ("Reservations", "canceled_at",
     "ALTER TABLE Reservations ADD COLUMN canceled_at DATETIME NULL AFTER updated_at"),
    ("Reservations", "canceled_by_user_id",
     "ALTER TABLE Reservations ADD COLUMN canceled_by_user_id INT NULL AFTER canceled_at"),
    ("Reservations", "reason",
     "ALTER TABLE Reservations ADD COLUMN reason TEXT NULL AFTER canceled_by_user_id"),
    ("Reservations", "rule_set_id",
     "ALTER TABLE Reservations ADD COLUMN rule_set_id INT NULL AFTER reason"),

    # Check_Ins
    ("Check_Ins", "method",
     "ALTER TABLE Check_Ins ADD COLUMN method VARCHAR(50) NULL AFTER checkin_time"),
    ("Check_Ins", "recorded_by_user_id",
     "ALTER TABLE Check_Ins ADD COLUMN recorded_by_user_id INT NULL AFTER method"),

    # Violations
    ("Violations", "notes",
     "ALTER TABLE Violations ADD COLUMN notes TEXT NULL AFTER status"),
    ("Violations", "resolved_at",
     "ALTER TABLE Violations ADD COLUMN resolved_at DATETIME NULL AFTER notes"),
    ("Violations", "resolved_by_user_id",
     "ALTER TABLE Violations ADD COLUMN resolved_by_user_id INT NULL AFTER resolved_at"),
]


def run():
    # Connect with autocommit=True so each DDL statement commits immediately.
    conn   = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=credentials.DB_HOST,
            port=credentials.DB_PORT,
            database=credentials.DB_NAME,
            user=credentials.DB_USER,
            password=credentials.DB_PASSWORD,
            autocommit=True,
        )
        cursor = conn.cursor()

        print("=== Creating tables (IF NOT EXISTS) ===")
        for stmt in CREATE_STATEMENTS:
            cursor.execute(stmt)
            print("  OK")

        print("\n=== Adding missing columns (safe ALTER) ===")
        for table, col, sql in ALTER_STATEMENTS:
            try:
                cursor.execute(sql)
                print(f"  Added {table}.{col}")
            except mysql.connector.Error as e:
                if e.errno == 1060:   # duplicate column — already exists, skip
                    print(f"  Already exists: {table}.{col}")
                else:
                    print(f"  ERROR on {table}.{col}: {e}")

        print("\nDatabase initialisation complete.")

    except Error as e:
        print(f"Connection/setup error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    run()

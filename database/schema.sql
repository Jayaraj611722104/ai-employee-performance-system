-- ============================================================
-- PulseHR — MySQL Production Schema
-- Compatible with app_mysql.py / database/models.py
-- Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS pulsehr
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE pulsehr;

-- ─── Users ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(10)  NOT NULL,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('employee','teamleader','hr','admin') NOT NULL,
    status        ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login    DATETIME,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Employees ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    user_id            VARCHAR(10)    NOT NULL,
    employee_id        VARCHAR(20)    NOT NULL UNIQUE,
    name               VARCHAR(100)   NOT NULL,
    role               VARCHAR(100)   NOT NULL,
    department         VARCHAR(100)   NOT NULL,
    skills             TEXT,
    experience         INT            NOT NULL DEFAULT 0,
    joining_date       DATE,
    projects_completed INT            NOT NULL DEFAULT 0,
    status             ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    team_leader_id     VARCHAR(10),
    team_id            VARCHAR(10),
    salary             DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_emp_user       FOREIGN KEY (user_id)        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_emp_tl         FOREIGN KEY (team_leader_id) REFERENCES users(id) ON DELETE SET NULL
    -- Note: fk_emp_team would reference teams(id), omitted here for simplicity in dropping tables
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Performance ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS performance (
    id                 INT          NOT NULL AUTO_INCREMENT,
    user_id            VARCHAR(10)  NOT NULL,
    productivity_score FLOAT        NOT NULL DEFAULT 0,
    attendance_pct     FLOAT        NOT NULL DEFAULT 0,
    task_completion    FLOAT        NOT NULL DEFAULT 0,
    quality_rating     FLOAT        NOT NULL DEFAULT 0,
    tl_score           FLOAT        NOT NULL DEFAULT 0,
    satisfaction       INT          NOT NULL DEFAULT 75,
    monthly_trend      TEXT,        -- JSON array, e.g. [70,72,74,76]
    month              VARCHAR(20),
    year               INT,
    recorded_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_perf_user FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Tasks ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tasks (
    id              VARCHAR(10)  NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    priority        ENUM('High','Medium','Low') NOT NULL DEFAULT 'Medium',
    deadline        DATE,
    required_skills TEXT,         -- JSON array
    assigned_to     VARCHAR(10),
    assigned_by     VARCHAR(10)  NOT NULL,
    status          ENUM('Pending','In Progress','Completed','Cancelled') NOT NULL DEFAULT 'Pending',
    progress        INT          NOT NULL DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_task_assignee FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_task_creator  FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Attendance ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id           INT         NOT NULL AUTO_INCREMENT,
    user_id      VARCHAR(10) NOT NULL,
    date         DATE        NOT NULL,
    status       ENUM('Present','Absent','Late','Leave') NOT NULL DEFAULT 'Present',
    check_in     TIME,
    check_out    TIME,
    hours_worked FLOAT       NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_attendance (user_id, date),
    CONSTRAINT fk_att_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Notifications ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id         INT         NOT NULL AUTO_INCREMENT,
    message    TEXT        NOT NULL,
    type       ENUM('info','success','warning','danger') NOT NULL DEFAULT 'info',
    target     VARCHAR(50) NOT NULL DEFAULT 'all',
    sent_by    VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_notif_sender FOREIGN KEY (sent_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Weekly Updates ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS weekly_updates (
    id                    INT         NOT NULL AUTO_INCREMENT,
    user_id               VARCHAR(10) NOT NULL,
    project_work          TEXT,
    tech_learned          VARCHAR(255),
    problems              TEXT,
    task_completion_level INT         NOT NULL DEFAULT 0,
    week_date             DATE,
    submitted_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_wu_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Login Logs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS login_logs (
    id         INT          NOT NULL AUTO_INCREMENT,
    user_id    VARCHAR(10),
    name       VARCHAR(100),
    role       VARCHAR(50),
    ip_address VARCHAR(50),
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Training ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS training (
    id              INT         NOT NULL AUTO_INCREMENT,
    user_id         VARCHAR(10) NOT NULL,
    week_number     INT,
    hours_completed FLOAT       NOT NULL DEFAULT 0,
    tech_learned    VARCHAR(255),
    problems        TEXT,
    completion_pct  INT         NOT NULL DEFAULT 0,
    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_train_user FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── AI Predictions Log ───────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_predictions (
    id              INT         NOT NULL AUTO_INCREMENT,
    user_id         VARCHAR(10),
    prediction_type ENUM('performance','promotion','attrition','skill_gap'),
    input_data      JSON,
    result_data     JSON,
    confidence      FLOAT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_pred_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Teams ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id                 VARCHAR(10)  NOT NULL,
    name               VARCHAR(100) NOT NULL,
    description        TEXT,
    leader_id          VARCHAR(10),
    project_name       VARCHAR(200),
    project_status     VARCHAR(50)  DEFAULT 'Not Started',
    project_completion INT          DEFAULT 0,
    score              INT          DEFAULT 0,
    monthly_scores     TEXT,        -- JSON array
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_team_leader FOREIGN KEY (leader_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Leave Requests ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_requests (
    id              VARCHAR(10) NOT NULL,
    user_id         VARCHAR(10) NOT NULL,
    employee_name   VARCHAR(100),
    department      VARCHAR(100),
    type            VARCHAR(50),
    from_date       DATE,
    to_date         DATE,
    days            INT,
    reason          TEXT,
    is_emergency    BOOLEAN DEFAULT FALSE,
    status          VARCHAR(50) DEFAULT 'Pending',
    applied_on      DATE,
    reviewed_by     VARCHAR(100),
    reviewed_at     DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_leave_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Team Performance ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_performance (
    id                 INT          NOT NULL AUTO_INCREMENT,
    team_id            VARCHAR(10)  NOT NULL,
    productivity_score FLOAT        NOT NULL DEFAULT 0,
    project_completion FLOAT        NOT NULL DEFAULT 0,
    quality_rating     FLOAT        NOT NULL DEFAULT 0,
    recorded_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_team_perf FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Team Project Status ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_projects (
    id                 INT          NOT NULL AUTO_INCREMENT,
    team_id            VARCHAR(10)  NOT NULL,
    project_name       VARCHAR(200) NOT NULL,
    status             VARCHAR(50)  DEFAULT 'Not Started',
    completion_pct     INT          DEFAULT 0,
    updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_team_proj FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── TL Employee Ratings ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS tl_ratings (
    id                 INT          NOT NULL AUTO_INCREMENT,
    employee_id        VARCHAR(10)  NOT NULL,
    tl_id              VARCHAR(10)  NOT NULL,
    rating             INT          NOT NULL DEFAULT 0,
    feedback           TEXT,
    recorded_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_rat_emp FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rat_tl  FOREIGN KEY (tl_id)       REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Team Member Task Completion ──────────────────────────────
CREATE TABLE IF NOT EXISTS team_member_tasks (
    id                 INT          NOT NULL AUTO_INCREMENT,
    team_id            VARCHAR(10)  NOT NULL,
    user_id            VARCHAR(10)  NOT NULL,
    tasks_completed    INT          DEFAULT 0,
    tasks_pending      INT          DEFAULT 0,
    updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_tmt_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_tmt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Helpful Indexes ──────────────────────────────────────
CREATE INDEX idx_perf_user    ON performance(user_id);
CREATE INDEX idx_tasks_to     ON tasks(assigned_to);
CREATE INDEX idx_tasks_by     ON tasks(assigned_by);
CREATE INDEX idx_attend_user  ON attendance(user_id);
CREATE INDEX idx_notif_target ON notifications(target);
CREATE INDEX idx_logs_user    ON login_logs(user_id);
CREATE INDEX idx_logs_time    ON login_logs(login_time);
CREATE INDEX idx_team_perf    ON team_performance(team_id);
CREATE INDEX idx_tl_rat_emp   ON tl_ratings(employee_id);

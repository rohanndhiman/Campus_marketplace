-- ============================================================
-- Campus Skill Marketplace System - Database Schema
-- ============================================================
-- Run this file in MySQL to set up the database.
-- Command: mysql -u root -p < database.sql
-- ============================================================

-- Create and select the database
CREATE DATABASE IF NOT EXISTS campus_marketplace;
USE campus_marketplace;

-- ============================================================
-- TABLE 1: Students
-- Stores all registered students (users of the system)
-- ============================================================
CREATE TABLE IF NOT EXISTS Students (
    student_id   INT AUTO_INCREMENT PRIMARY KEY,   -- Unique ID for each student
    name         VARCHAR(100) NOT NULL,             -- Full name
    email        VARCHAR(100) NOT NULL UNIQUE,      -- College email (used for login)
    password     VARCHAR(255) NOT NULL,             -- Hashed password
    branch       VARCHAR(100) NOT NULL,             -- e.g., CSE, ECE, MBA
    year         INT NOT NULL,                      -- 1, 2, 3, or 4
    bio          TEXT,                              -- Short self-description
    is_admin     BOOLEAN DEFAULT FALSE,             -- Admin role flag
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: Skills
-- Master list of skills available in the system
-- ============================================================
CREATE TABLE IF NOT EXISTS Skills (
    skill_id     INT AUTO_INCREMENT PRIMARY KEY,   -- Unique ID for each skill
    skill_name   VARCHAR(100) NOT NULL UNIQUE,      -- e.g., Python, Photoshop
    category     VARCHAR(100)                       -- e.g., Programming, Design
);

-- ============================================================
-- TABLE 3: Student_Skills
-- Maps which student has which skill (many-to-many relationship)
-- ============================================================
CREATE TABLE IF NOT EXISTS Student_Skills (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT NOT NULL,                     -- FK → Students
    skill_id     INT NOT NULL,                     -- FK → Skills
    is_verified  BOOLEAN DEFAULT FALSE,            -- Admin can mark as verified
    FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)   REFERENCES Skills(skill_id)   ON DELETE CASCADE,
    UNIQUE (student_id, skill_id)                  -- A student can't add same skill twice
);

-- ============================================================
-- TABLE 4: Service_Requests
-- Tasks posted by students who need help
-- ============================================================
CREATE TABLE IF NOT EXISTS Service_Requests (
    request_id   INT AUTO_INCREMENT PRIMARY KEY,
    posted_by    INT NOT NULL,                     -- FK → Students (who posted)
    skill_id     INT NOT NULL,                     -- Skill needed for this task
    title        VARCHAR(200) NOT NULL,            -- Short title of the task
    description  TEXT,                             -- Detailed description
    status       ENUM('Open','Assigned','Completed') DEFAULT 'Open',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES Students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)  REFERENCES Skills(skill_id)    ON DELETE CASCADE
);

-- ============================================================
-- TABLE 5: Transactions
-- Records which student is assigned to which task
-- ============================================================
CREATE TABLE IF NOT EXISTS Transactions (
    txn_id       INT AUTO_INCREMENT PRIMARY KEY,
    request_id   INT NOT NULL,                     -- FK → Service_Requests
    assigned_to  INT NOT NULL,                     -- FK → Students (who does the task)
    assigned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_status  ENUM('Pending','In Progress','Completed') DEFAULT 'Pending',
    FOREIGN KEY (request_id)  REFERENCES Service_Requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES Students(student_id)         ON DELETE CASCADE
);

-- ============================================================
-- TABLE 6: Feedback
-- Rating and comments given after task completion
-- ============================================================
CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id   INT AUTO_INCREMENT PRIMARY KEY,
    txn_id        INT NOT NULL,                    -- FK → Transactions
    given_by      INT NOT NULL,                    -- FK → Students (who gives feedback)
    rating        INT CHECK (rating BETWEEN 1 AND 5), -- 1 to 5 stars
    comment       TEXT,                            -- Optional comment
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (txn_id)    REFERENCES Transactions(txn_id)   ON DELETE CASCADE,
    FOREIGN KEY (given_by)  REFERENCES Students(student_id)   ON DELETE CASCADE,
    UNIQUE (txn_id, given_by)                      -- One feedback per transaction per user
);

-- ============================================================
-- SAMPLE DATA for Testing
-- ============================================================

-- Insert Skills
INSERT INTO Skills (skill_name, category) VALUES
    ('Python',          'Programming'),
    ('Java',            'Programming'),
    ('Web Development', 'Programming'),
    ('Graphic Design',  'Design'),
    ('Video Editing',   'Media'),
    ('Data Analysis',   'Analytics'),
    ('Machine Learning','AI/ML'),
    ('UI/UX Design',    'Design'),
    ('Content Writing', 'Writing'),
    ('Photography',     'Media');

-- Insert Students (passwords are plain text here for demo; app uses hashing)
-- Password for all: password123
INSERT INTO Students (name, email, password, branch, year, bio, is_admin) VALUES
    ('Rohan Sharma',   'rohan@college.edu',   'pbkdf2:sha256:260000$demo$hash1', 'CSE', 3, 'I love coding and problem solving.', TRUE),
    ('Priya Mehta',    'priya@college.edu',   'pbkdf2:sha256:260000$demo$hash2', 'Design', 2, 'Creative designer with 2 years experience.', FALSE),
    ('Arjun Singh',    'arjun@college.edu',   'pbkdf2:sha256:260000$demo$hash3', 'ECE', 4, 'Final year student, expert in ML.', FALSE),
    ('Neha Kapoor',    'neha@college.edu',    'pbkdf2:sha256:260000$demo$hash4', 'MBA', 1, 'Good at content writing and marketing.', FALSE);

-- Assign Skills to Students
INSERT INTO Student_Skills (student_id, skill_id, is_verified) VALUES
    (1, 1, TRUE),   -- Rohan: Python (verified)
    (1, 3, FALSE),  -- Rohan: Web Dev (unverified)
    (2, 4, TRUE),   -- Priya: Graphic Design (verified)
    (2, 8, FALSE),  -- Priya: UI/UX Design
    (3, 7, TRUE),   -- Arjun: Machine Learning (verified)
    (3, 6, TRUE),   -- Arjun: Data Analysis (verified)
    (4, 9, FALSE);  -- Neha: Content Writing

-- ============================================================
-- END OF SCHEMA
-- ============================================================

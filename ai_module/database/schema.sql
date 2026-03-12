-- ai_module/database/schema.sql
-- Database Schema for AI-Based Employee Performance Prediction and Promotion Recommendation System

CREATE DATABASE IF NOT EXISTS pulsehr_ai;
USE pulsehr_ai;

-- Employees Table
CREATE TABLE IF NOT EXISTS employees (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50),
    department VARCHAR(50),
    experience_years INT DEFAULT 0,
    joining_date DATE,
    salary DECIMAL(12, 2),
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- Attendance Table (Detailed daily tracking)
CREATE TABLE IF NOT EXISTS daily_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Leave') DEFAULT 'Present',
    check_in_time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
);

-- Legacy Monthly Attendance (keeping for backward compatibility if needed)
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    month_name VARCHAR(20),
    present_days INT DEFAULT 0,
    total_working_days INT DEFAULT 22,
    FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
);

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(200),
    assigned_to VARCHAR(50),
    status ENUM('Pending', 'In Progress', 'Completed', 'At Risk') DEFAULT 'Pending',
    bug_count INT DEFAULT 0,
    rework_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (assigned_to) REFERENCES employees(user_id) ON DELETE CASCADE
);

-- Performance Reviews Table
CREATE TABLE IF NOT EXISTS performance_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    manager_rating INT CHECK (manager_rating BETWEEN 1 AND 5),
    peer_review_score DECIMAL(5, 2) CHECK (peer_review_score BETWEEN 0 AND 100),
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
);

-- Productivity Scores Table
CREATE TABLE IF NOT EXISTS productivity_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    attendance_score DECIMAL(5, 2),
    task_completion_rate DECIMAL(5, 2),
    quality_score DECIMAL(5, 2),
    peer_review_score DECIMAL(5, 2),
    final_productivity_score DECIMAL(5, 2),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
);

-- Promotion Predictions Table
CREATE TABLE IF NOT EXISTS promotion_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    predicted_level ENUM('Excellent', 'Good', 'Average', 'Needs Improvement'),
    promotion_status ENUM('Recommended', 'Not Recommended'),
    probability DECIMAL(5, 2),
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees(user_id) ON DELETE CASCADE
);

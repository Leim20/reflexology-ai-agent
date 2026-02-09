-- ============================================================================
-- MySQL Setup for Booking Session Management
-- Replaces Redis for booking sessions to prevent hallucination issues
-- ============================================================================

-- Create database (run as root)
CREATE DATABASE IF NOT EXISTS reflexology_booking
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE reflexology_booking;

-- ============================================================================
-- BOOKING SESSIONS TABLE
-- Stores active booking sessions with all fields
-- ============================================================================
CREATE TABLE IF NOT EXISTS booking_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL UNIQUE,

    -- Booking fields
    customer_name VARCHAR(100) DEFAULT NULL,
    customer_gender ENUM('Male', 'Female') DEFAULT NULL,
    service VARCHAR(200) DEFAULT NULL,
    date DATE DEFAULT NULL,
    time TIME DEFAULT NULL,
    therapist_gender ENUM('Male', 'Female') DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    pain_point TEXT DEFAULT NULL,

    -- Flow control flags
    pain_point_asked BOOLEAN DEFAULT FALSE,
    personal_info_asked BOOLEAN DEFAULT FALSE,

    -- Session metadata
    status ENUM('active', 'completed', 'expired', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT NULL,

    -- Indexes for fast lookups
    INDEX idx_session_id (session_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    INDEX idx_phone (phone)
) ENGINE=InnoDB;

-- ============================================================================
-- SESSION HISTORY TABLE
-- Archives completed/expired sessions for analytics
-- ============================================================================
CREATE TABLE IF NOT EXISTS booking_session_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,

    -- Booking fields (same as booking_sessions)
    customer_name VARCHAR(100) DEFAULT NULL,
    customer_gender ENUM('Male', 'Female') DEFAULT NULL,
    service VARCHAR(200) DEFAULT NULL,
    date DATE DEFAULT NULL,
    time TIME DEFAULT NULL,
    therapist_gender ENUM('Male', 'Female') DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    pain_point TEXT DEFAULT NULL,

    -- Session outcome
    final_status ENUM('completed', 'expired', 'cancelled') NOT NULL,

    -- Timestamps
    session_created_at TIMESTAMP NULL,
    session_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- For analytics
    total_messages INT DEFAULT 0,
    fields_collected INT DEFAULT 0,

    INDEX idx_phone (phone),
    INDEX idx_completed_at (session_completed_at),
    INDEX idx_final_status (final_status)
) ENGINE=InnoDB;

-- ============================================================================
-- FIELD VALIDATION LOG TABLE
-- Logs Two-Phase validation results for debugging
-- ============================================================================
CREATE TABLE IF NOT EXISTS field_validation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,

    -- Validation details
    field_name VARCHAR(50) NOT NULL,
    extracted_value TEXT,
    validation_result ENUM('valid', 'hallucinated', 'invalid_format') NOT NULL,

    -- Context
    user_message TEXT,
    validation_reason TEXT,

    -- Timestamp
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session_id (session_id),
    INDEX idx_validation_result (validation_result),
    INDEX idx_validated_at (validated_at)
) ENGINE=InnoDB;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- Procedure to clean expired sessions (run periodically)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_expired_sessions()
BEGIN
    -- Archive expired sessions
    INSERT INTO booking_session_history (
        session_id, customer_name, customer_gender, service, date, time,
        therapist_gender, phone, pain_point, final_status,
        session_created_at, fields_collected
    )
    SELECT
        session_id, customer_name, customer_gender, service, date, time,
        therapist_gender, phone, pain_point, 'expired',
        created_at,
        (CASE WHEN customer_name IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN customer_gender IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN service IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN date IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN time IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN therapist_gender IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END)
    FROM booking_sessions
    WHERE status = 'active' AND expires_at < NOW();

    -- Delete expired sessions
    DELETE FROM booking_sessions
    WHERE status = 'active' AND expires_at < NOW();
END //
DELIMITER ;

-- Procedure to get or create session with expiry logic
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS get_or_create_session(
    IN p_session_id VARCHAR(100),
    OUT p_is_new BOOLEAN,
    OUT p_needs_confirmation BOOLEAN,
    OUT p_hours_since_update DECIMAL(10,2)
)
BEGIN
    DECLARE v_updated_at TIMESTAMP;
    DECLARE v_hours DECIMAL(10,2);

    -- Check if session exists
    SELECT updated_at INTO v_updated_at
    FROM booking_sessions
    WHERE session_id = p_session_id AND status = 'active'
    LIMIT 1;

    IF v_updated_at IS NULL THEN
        -- New session
        INSERT INTO booking_sessions (session_id, expires_at)
        VALUES (p_session_id, DATE_ADD(NOW(), INTERVAL 24 HOUR));

        SET p_is_new = TRUE;
        SET p_needs_confirmation = FALSE;
        SET p_hours_since_update = 0;
    ELSE
        -- Existing session - calculate hours since last update
        SET v_hours = TIMESTAMPDIFF(SECOND, v_updated_at, NOW()) / 3600.0;
        SET p_hours_since_update = v_hours;
        SET p_is_new = FALSE;

        -- Session expiry logic:
        -- < 1 hour: auto-continue (no confirmation needed)
        -- 1-24 hours: auto-continue (no confirmation needed)
        -- > 24 hours: needs user confirmation
        IF v_hours > 24 THEN
            SET p_needs_confirmation = TRUE;
        ELSE
            SET p_needs_confirmation = FALSE;
            -- Refresh expiry
            UPDATE booking_sessions
            SET expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)
            WHERE session_id = p_session_id;
        END IF;
    END IF;
END //
DELIMITER ;

-- ============================================================================
-- EVENT SCHEDULER (for automatic cleanup)
-- ============================================================================
-- Enable event scheduler (run as root if not already enabled)
-- SET GLOBAL event_scheduler = ON;

CREATE EVENT IF NOT EXISTS cleanup_expired_booking_sessions
ON SCHEDULE EVERY 1 HOUR
DO CALL cleanup_expired_sessions();

-- ============================================================================
-- INITIAL USER SETUP (adjust password as needed)
-- ============================================================================
-- CREATE USER IF NOT EXISTS 'reflexology_app'@'localhost' IDENTIFIED BY 'your_secure_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON reflexology_booking.* TO 'reflexology_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE reflexology_booking.cleanup_expired_sessions TO 'reflexology_app'@'localhost';
-- GRANT EXECUTE ON PROCEDURE reflexology_booking.get_or_create_session TO 'reflexology_app'@'localhost';
-- FLUSH PRIVILEGES;

from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `user_consents` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `consent_type` VARCHAR(50) NOT NULL COMMENT 'TERMS_OF_SERVICE: TERMS_OF_SERVICE\nPRIVACY_POLICY: PRIVACY_POLICY\nMEDICAL_DATA: MEDICAL_DATA\nMARKETING: MARKETING',
    `agreed` BOOL NOT NULL,
    `version` VARCHAR(20) NOT NULL,
    `agreed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `withdrawn_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_con_users_4a5cdd72` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `accessibility_settings` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `font_size` VARCHAR(20) NOT NULL COMMENT 'SMALL: SMALL\nMEDIUM: MEDIUM\nLARGE: LARGE\nXLARGE: XLARGE' DEFAULT 'MEDIUM',
    `tts_enabled` BOOL NOT NULL DEFAULT 0,
    `easy_language` BOOL NOT NULL DEFAULT 0,
    `guardian_share_enabled` BOOL NOT NULL DEFAULT 0,
    `location_tracking_enabled` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_accessib_users_09246b14` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `diary_medication_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `log_date` DATE NOT NULL,
    `drug_name` VARCHAR(200) NOT NULL,
    `time_slot` VARCHAR(20) COMMENT 'MORNING: MORNING\nLUNCH: LUNCH\nDINNER: DINNER\nBEDTIME: BEDTIME',
    `taken` BOOL NOT NULL DEFAULT 1,
    `taken_time` DATETIME(6),
    `notes` LONGTEXT,
    `latitude` DECIMAL(10,4),
    `longitude` DECIMAL(10,4),
    `location_recorded_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_diary_me_users_bc0b4b94` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `diary_symptom_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `log_date` DATE NOT NULL,
    `overall_condition` VARCHAR(20) NOT NULL COMMENT 'VERY_BAD: VERY_BAD\nBAD: BAD\nNORMAL: NORMAL\nGOOD: GOOD\nVERY_GOOD: VERY_GOOD',
    `body_parts` JSON,
    `feeling` JSON,
    `memo` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_diary_sy_users_2491f500` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `emergency_cards` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `blood_type` VARCHAR(10),
    `allergies` LONGTEXT,
    `chronic_conditions` LONGTEXT,
    `emergency_contacts` JSON,
    `siren_mode` VARCHAR(20) NOT NULL COMMENT 'NORMAL: NORMAL\nSILENT: SILENT\nOFF: OFF' DEFAULT 'NORMAL',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_emergenc_users_72a898e0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `health_metrics` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `metric_type` VARCHAR(30) NOT NULL COMMENT 'BLOOD_PRESSURE: BLOOD_PRESSURE\nBLOOD_SUGAR: BLOOD_SUGAR\nWEIGHT: WEIGHT\nHEART_RATE: HEART_RATE',
    `user_recorded_value` DECIMAL(10,2) NOT NULL,
    `measured_at` DATETIME(6) NOT NULL,
    `notes` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_health_m_users_769d851c` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `feedback_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `target_type` VARCHAR(20) NOT NULL COMMENT 'GUIDE: GUIDE\nCHAT: CHAT\nOCR: OCR\nPILL: PILL',
    `target_id` CHAR(36) NOT NULL,
    `feedback_type` VARCHAR(20) NOT NULL COMMENT 'RATING: RATING\nTHUMBS_UP: THUMBS_UP\nTHUMBS_DOWN: THUMBS_DOWN\nREGENERATE: REGENERATE',
    `rating` INT,
    `comment` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_feedback_users_2eb526a4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `notifications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `notification_type` VARCHAR(30) NOT NULL COMMENT 'MEDICATION: MEDICATION\nDIARY: DIARY\nHEALTH_METRIC: HEALTH_METRIC\nEMERGENCY: EMERGENCY\nGUIDE: GUIDE',
    `title` VARCHAR(200) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `is_read` BOOL NOT NULL DEFAULT 0,
    `scheduled_at` DATETIME(6) NOT NULL,
    `sent_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_notifica_users_ca29871f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `notification_settings` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `medication_enabled` BOOL NOT NULL DEFAULT 1,
    `diary_enabled` BOOL NOT NULL DEFAULT 1,
    `health_metric_enabled` BOOL NOT NULL DEFAULT 1,
    `emergency_enabled` BOOL NOT NULL DEFAULT 1,
    `quiet_hours_start` TIME(6),
    `quiet_hours_end` TIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_notifica_users_ea1f99f3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `pharmacies` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL,
    `address` VARCHAR(500) NOT NULL,
    `phone` VARCHAR(20),
    `latitude` DECIMAL(10,7) NOT NULL,
    `longitude` DECIMAL(10,7) NOT NULL,
    `operating_hours` JSON,
    `is_24h_available` BOOL NOT NULL DEFAULT 0,
    `is_holiday_available` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `favorite_places` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `place_type` VARCHAR(20) NOT NULL COMMENT 'HOSPITAL: HOSPITAL\nPHARMACY: PHARMACY',
    `name` VARCHAR(200) NOT NULL,
    `address` VARCHAR(500),
    `phone` VARCHAR(20),
    `memo` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_favorite_users_2bae7c72` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `medical_appointments` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `appointment_date` DATETIME(6) NOT NULL,
    `hospital_name` VARCHAR(200) NOT NULL,
    `doctor_name` VARCHAR(100),
    `purpose` VARCHAR(200),
    `notes` LONGTEXT,
    `notification_enabled` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_64c49d52` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `guardians` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `phone_number` VARCHAR(20),
    `email` VARCHAR(100),
    `relationship` VARCHAR(50),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_guardian_users_216ee0a6` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `share_links` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `token` VARCHAR(100) NOT NULL UNIQUE,
    `duration` VARCHAR(30) NOT NULL COMMENT 'ONE_DAY: ONE_DAY\nONE_WEEK: ONE_WEEK\nONE_MONTH: ONE_MONTH\nUNTIL_REVOKED: UNTIL_REVOKED',
    `categories` JSON NOT NULL,
    `include_summary_only` BOOL NOT NULL DEFAULT 1,
    `expires_at` DATETIME(6) NOT NULL,
    `is_revoked` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `guardian_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_share_li_guardian_5f30bd4f` FOREIGN KEY (`guardian_id`) REFERENCES `guardians` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_share_li_users_fa56d203` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `share_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `viewed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `viewer_ip` VARCHAR(50),
    `share_link_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_share_lo_share_li_41c3d41b` FOREIGN KEY (`share_link_id`) REFERENCES `share_links` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prompts` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `prompt_type` VARCHAR(50) NOT NULL COMMENT 'HEALTH_GUIDE: HEALTH_GUIDE\nOCR_EXTRACT: OCR_EXTRACT\nOCR_STRUCTURE: OCR_STRUCTURE\nMEDICATION_INFO: MEDICATION_INFO',
    `name` VARCHAR(200) NOT NULL,
    `version` VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    `template_text` LONGTEXT NOT NULL,
    `variables` JSON,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_prompts_prompt__d4c8d3` (`prompt_type`, `version`)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `health_guide_contents` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `guide_type` VARCHAR(50) NOT NULL COMMENT 'EXERCISE: EXERCISE\nDIET: DIET\nLIFESTYLE: LIFESTYLE\nMEDICATION: MEDICATION\nGENERAL: GENERAL',
    `status` VARCHAR(30) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `user_question` LONGTEXT NOT NULL,
    `guide_content` LONGTEXT,
    `prompt_used_id` CHAR(36),
    `metadata` JSON,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_health_g_users_a1cb2840` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prescriptions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `ocr_raw_text` LONGTEXT,
    `image_url` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_prescrip_users_75d98828` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `medications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `drug_name_user_input` VARCHAR(200) NOT NULL,
    `dosage` VARCHAR(50),
    `frequency` VARCHAR(50),
    `duration_days` INT,
    `start_date` DATE,
    `end_date` DATE,
    `is_autoimmune_drug` BOOL NOT NULL DEFAULT 0,
    `drug_category` VARCHAR(50),
    `notes` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `prescription_id` CHAR(36),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medicati_prescrip_1f35ac11` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_medicati_users_5f6773a0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_consents`;
        DROP TABLE IF EXISTS `notifications`;
        DROP TABLE IF EXISTS `prompts`;
        DROP TABLE IF EXISTS `favorite_places`;
        DROP TABLE IF EXISTS `diary_symptom_logs`;
        DROP TABLE IF EXISTS `notification_settings`;
        DROP TABLE IF EXISTS `health_guide_contents`;
        DROP TABLE IF EXISTS `share_links`;
        DROP TABLE IF EXISTS `medical_appointments`;
        DROP TABLE IF EXISTS `guardians`;
        DROP TABLE IF EXISTS `accessibility_settings`;
        DROP TABLE IF EXISTS `prescriptions`;
        DROP TABLE IF EXISTS `pharmacies`;
        DROP TABLE IF EXISTS `health_metrics`;
        DROP TABLE IF EXISTS `emergency_cards`;
        DROP TABLE IF EXISTS `diary_medication_logs`;
        DROP TABLE IF EXISTS `medications`;
        DROP TABLE IF EXISTS `share_logs`;
        DROP TABLE IF EXISTS `feedback_logs`;"""


MODELS_STATE = (
    "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"
    "aljmI="
)

from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(40) NOT NULL,
    `hashed_password` VARCHAR(128) NOT NULL,
    `name` VARCHAR(20) NOT NULL,
    `gender` VARCHAR(6) NOT NULL COMMENT 'MALE: MALE\nFEMALE: FEMALE',
    `birthday` DATE NOT NULL,
    `phone_number` VARCHAR(11) NOT NULL,
    `height` DOUBLE,
    `weight` DOUBLE,
    `mode` VARCHAR(16) NOT NULL COMMENT 'GENERAL: general\nAUTOIMMUNE: autoimmune' DEFAULT 'general',
    `mode_selected_at` DATETIME(6),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_admin` BOOL NOT NULL DEFAULT 0,
    `last_login` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `knowledge_base` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `status` VARCHAR(10) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nDONE: DONE\nFAILED: FAILED' DEFAULT 'PENDING',
    `chunk_count` INT,
    `source_organization` VARCHAR(100) NOT NULL,
    `published_year` SMALLINT NOT NULL,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `uploaded_by_user_id` BIGINT NOT NULL,
    UNIQUE KEY `uid_knowledge_b_title_ab92ff` (`title`, `source_organization`, `published_year`),
    CONSTRAINT `fk_knowledg_users_de6f71a5` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_knowledge_b_status_3e2bc0` (`status`),
    KEY `idx_knowledge_b_uploade_65f25d` (`uploaded_by_user_id`),
    KEY `idx_knowledge_b_created_82eded` (`created_at`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `health_guides` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `status` VARCHAR(30) NOT NULL,
    `medication_general` LONGTEXT NOT NULL,
    `side_effect_monitoring` JSON NOT NULL,
    `lifestyle_info` LONGTEXT NOT NULL,
    `symptom_summary` LONGTEXT NOT NULL,
    `sources` JSON NOT NULL,
    `disclaimer` LONGTEXT NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_diseases` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `disease_code` VARCHAR(20) NOT NULL COMMENT 'RA: RA\nSLE: SLE\nDM1: DM1\nDM2: DM2\nHTN: HTN\nHYPERLIPIDEMIA: HYPERLIPIDEMIA\nASTHMA: ASTHMA\nCOPD: COPD\nPARKINSON: PARKINSON\nMS: MS\nBREAST_CANCER: BREAST_CANCER\nCOLON_CANCER: COLON_CANCER\nLUNG_CANCER: LUNG_CANCER',
    `diagnosed_date` DATE,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_dis_users_d457ee90` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-DISE-001/002 — 자가면역 모드 사용자의 등록 질환.';
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(64) NOT NULL,
    `detail` JSON,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_audit_lo_users_4188f9a7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='NFR-COMPLI-004 — 민감정보 처리 감사 로그 (append-only).';
CREATE TABLE IF NOT EXISTS `user_risk_profiles` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `pregnancy_status` VARCHAR(16) NOT NULL COMMENT 'NONE: NONE\nPREGNANT: PREGNANT\nBREASTFEEDING: BREASTFEEDING\nPLANNING: PLANNING' DEFAULT 'NONE',
    `renal_impairment` BOOL NOT NULL DEFAULT 0,
    `hepatic_impairment` BOOL NOT NULL DEFAULT 0,
    `infection_history` LONGTEXT,
    `drug_allergy` LONGTEXT,
    `comorbidities` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_user_ris_users_911480e2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-001 — 자가면역 안내문 생성용 위험요인 프로필 (사용자당 1개).';
CREATE TABLE IF NOT EXISTS `user_medications` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(128) NOT NULL,
    `drug_class` VARCHAR(24) NOT NULL COMMENT 'STEROID: STEROID\nIMMUNOSUPPRESSANT: IMMUNOSUPPRESSANT\nANTIMALARIAL: ANTIMALARIAL\nBIOLOGIC: BIOLOGIC\nNSAID: NSAID',
    `is_injection` BOOL NOT NULL DEFAULT 0,
    `end_date` DATE,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_med_users_e877c4e6` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-002 — 사용자가 등록한 자가면역 관련 약물.';
CREATE TABLE IF NOT EXISTS `disease_activity_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `log_date` DATE NOT NULL,
    `pain_vas` INT NOT NULL,
    `fatigue` INT NOT NULL,
    `morning_stiffness_min` INT,
    `joint_swelling_areas` JSON,
    `daily_difficulty` INT NOT NULL,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    UNIQUE KEY `uid_disease_act_user_id_21c8d9` (`user_id`, `log_date`),
    CONSTRAINT `fk_disease__users_54d06ecb` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-ACTV-001 — 자가면역질환 공통 활성도 정량 일일 기록 (사용자·일자당 1건).';
CREATE TABLE IF NOT EXISTS `symptom_check_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `checked_symptoms` JSON NOT NULL,
    `red_flag_triggered` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_symptom__users_bf034718` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-SYMP-001 — 위험 증상 자가체크 기록. red_flag_triggered는 SYMP-002 룰 매칭 결과.';
CREATE TABLE IF NOT EXISTS `activity_alert_settings` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `pain_threshold` INT,
    `pain_consecutive_days` INT,
    `morning_stiffness_threshold` INT,
    `fatigue_threshold` INT,
    `alert_message` LONGTEXT NOT NULL,
    `is_enabled` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_activity_users_891c1cc4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-ACTV-003 — 사용자가 직접 설정한 활성도 자가 모니터링 알림 기준 (사용자당 1개).';
CREATE TABLE IF NOT EXISTS `medical_schedules` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `schedule_type` VARCHAR(16) NOT NULL COMMENT 'BLOOD_TEST: BLOOD_TEST\nURINE_TEST: URINE_TEST\nEYE_EXAM: EYE_EXAM\nAPPOINTMENT: APPOINTMENT\nINJECTION: INJECTION',
    `title` VARCHAR(200),
    `scheduled_date` DATE NOT NULL,
    `reminder_days_before` INT NOT NULL DEFAULT 1,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_8614df87` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-004 — 자가면역 관리 의료 일정 (검사·진료·주사).';
CREATE TABLE IF NOT EXISTS `lab_references` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `code` VARCHAR(64) NOT NULL UNIQUE,
    `name_ko` VARCHAR(128) NOT NULL,
    `abbr` VARCHAR(64),
    `category` VARCHAR(64),
    `description` VARCHAR(255),
    `unit` VARCHAR(32),
    `reference_range_general` VARCHAR(255),
    `reference_note` VARCHAR(255),
    `source` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `lab_results` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `test_date` DATE NOT NULL,
    `test_item` VARCHAR(128) NOT NULL,
    `value` VARCHAR(64) NOT NULL,
    `reference_range` VARCHAR(64),
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_lab_resu_users_6c32f6c9` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-LAB-001 — 사용자가 직접 입력한 검사 결과 (수동 입력·보관).';
CREATE TABLE IF NOT EXISTS `lupus_skin_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `symptom_type` VARCHAR(16) NOT NULL COMMENT 'RASH: RASH\nORAL_ULCER: ORAL_ULCER\nHAIR_LOSS: HAIR_LOSS\nRAYNAUD: RAYNAUD',
    `log_date` DATE NOT NULL,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_lupus_sk_users_b213a5b4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-LUPUS-001 — SLE 특이 피부 증상 기록 (순수 저장, 해석 없음).';
CREATE TABLE IF NOT EXISTS `lupus_daily_contexts` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `log_date` DATE NOT NULL,
    `uv_exposure_minutes` INT,
    `sleep_hours` DOUBLE,
    `stress_level` VARCHAR(8) COMMENT 'LOW: LOW\nMID: MID\nHIGH: HIGH',
    `med_taken` BOOL,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    UNIQUE KEY `uid_lupus_daily_user_id_c17419` (`user_id`, `log_date`),
    CONSTRAINT `fk_lupus_da_users_66615162` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-LUPUS-001 — SLE 환자 생활 맥락 일일 기록 (순수 저장, 해석·판정 없음). 사용자·일자당 1건.';
CREATE TABLE IF NOT EXISTS `chat_sessions` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `mode` VARCHAR(16) NOT NULL COMMENT 'GENERAL: GENERAL\nAUTOIMMUNE: AUTOIMMUNE',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chat_ses_users_520002c0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `role` VARCHAR(16) NOT NULL COMMENT 'USER: USER\nASSISTANT: ASSISTANT',
    `content` LONGTEXT NOT NULL,
    `rag_sources` JSON NOT NULL,
    `blocked_by_filter` BOOL NOT NULL DEFAULT 0,
    `block_reason` VARCHAR(64),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `session_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chat_mes_chat_ses_0d4a2737` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_feedbacks` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `score` INT NOT NULL,
    `comment` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `message_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chat_fee_chat_mes_a116c643` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_consents` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `consent_type` VARCHAR(50) NOT NULL COMMENT 'TERMS_OF_SERVICE: TERMS_OF_SERVICE\nPRIVACY_POLICY: PRIVACY_POLICY\nMEDICAL_DATA: MEDICAL_DATA\nMARKETING: MARKETING\nMODEL_IMPROVEMENT: MODEL_IMPROVEMENT',
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
    `notification_type` VARCHAR(30) NOT NULL COMMENT 'MEDICATION: MEDICATION\nDIARY: DIARY\nHEALTH_METRIC: HEALTH_METRIC\nEMERGENCY: EMERGENCY\nGUIDE: GUIDE\nSCHEDULE: SCHEDULE',
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
CREATE TABLE IF NOT EXISTS `medical_documents` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `document_type` VARCHAR(20) NOT NULL COMMENT 'prescription: prescription\nmedical_record: medical_record\npill_bag: pill_bag\nlab_result: lab_result\nhealth_checkup: health_checkup\nother: other',
    `file_path` VARCHAR(500) NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `stored_filename` VARCHAR(100) NOT NULL,
    `file_size` INT,
    `mime_type` VARCHAR(100),
    `upload_status` VARCHAR(20) NOT NULL COMMENT 'uploaded: uploaded\nconfirmed: confirmed\ndeleted: deleted' DEFAULT 'uploaded',
    `is_user_confirmed` BOOL NOT NULL DEFAULT 0,
    `confirmed_data` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_9d9be28d` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `ocr_jobs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(20) NOT NULL COMMENT 'pending: pending\nprocessing: processing\ncompleted: completed\nfailed: failed' DEFAULT 'pending',
    `raw_text` LONGTEXT,
    `structured_data` LONGTEXT,
    `confidence_score` DOUBLE,
    `field_confidences` LONGTEXT,
    `error_message` VARCHAR(500),
    `started_at` DATETIME(6),
    `completed_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `document_id` INT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_ocr_jobs_medical__2dba6c0e` FOREIGN KEY (`document_id`) REFERENCES `medical_documents` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ocr_jobs_users_1ad1c7c0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
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
    `image_s3_url` LONGTEXT NOT NULL,
    `ocr_raw_text` LONGTEXT,
    `ocr_status` VARCHAR(20) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `user_confirmed` BOOL NOT NULL DEFAULT 0,
    `prescription_date` DATE,
    `hospital_name` VARCHAR(100),
    `diagnosis_text` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `document_id` INT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_prescrip_medical__7df49791` FOREIGN KEY (`document_id`) REFERENCES `medical_documents` (`id`) ON DELETE SET NULL,
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
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `risk_flags` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `source_type` VARCHAR(16) NOT NULL COMMENT 'SYMPTOM_CHECK: SYMPTOM_CHECK\nRISK_PROFILE: RISK_PROFILE\nLAB_RESULT: LAB_RESULT',
    `source_id` BIGINT,
    `flag_code` VARCHAR(64) NOT NULL,
    `flag_label` VARCHAR(128) NOT NULL,
    `category` VARCHAR(32) NOT NULL,
    `message` LONGTEXT NOT NULL,
    `red_flag` BOOL NOT NULL DEFAULT 0,
    `consultation_recommended` BOOL NOT NULL DEFAULT 1,
    `status` VARCHAR(16) NOT NULL COMMENT 'ACTIVE: ACTIVE\nRESOLVED: RESOLVED\nDISMISSED: DISMISSED' DEFAULT 'ACTIVE',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_risk_fla_users_95269dc4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-006 — 고위험 플래그 저장소. 게이트 엔진 매칭 결과를 DB에 영속.';
CREATE TABLE IF NOT EXISTS `autoimmune_profiles` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `risk_factors` JSON NOT NULL,
    `pregnancy_status` VARCHAR(16) NOT NULL COMMENT 'NONE: none\nPREGNANT: pregnant\nBREASTFEEDING: breastfeeding\nPLANNING: planning' DEFAULT 'none',
    `vaccination_history` JSON NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_autoimmu_users_83724aa4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `auto_guides` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(24) NOT NULL COMMENT 'GENERATED: GENERATED\nBLOCKED_HIGH_RISK: BLOCKED_HIGH_RISK\nGENERATION_FAILED: GENERATION_FAILED',
    `medication_general` LONGTEXT NOT NULL,
    `side_effect_monitoring` JSON NOT NULL,
    `lifestyle_info` LONGTEXT NOT NULL,
    `symptom_summary` LONGTEXT NOT NULL,
    `sources` JSON NOT NULL,
    `disclaimer` LONGTEXT NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_auto_gui_users_62041970` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-005 — 자가면역 맞춤 안내문 생성 결과 영속화.';
CREATE TABLE IF NOT EXISTS `guide_generation_jobs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(20) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nCOMPLETED: COMPLETED\nBLOCKED: BLOCKED\nFAILED: FAILED' DEFAULT 'PENDING',
    `trigger_type` VARCHAR(20) NOT NULL,
    `blocked_reason` VARCHAR(40),
    `trigger_emergency_modal` BOOL NOT NULL DEFAULT 0,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `guide_id` BIGINT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_guide_ge_auto_gui_5fb3fa1d` FOREIGN KEY (`guide_id`) REFERENCES `auto_guides` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_guide_ge_users_4ebc89ac` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `pre_consultation_reports` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(20) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `visit_date` DATE NOT NULL,
    `period_days` INT NOT NULL DEFAULT 90,
    `pdf` LONGBLOB,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_pre_cons_users_a207beb8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `report_shares` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `recipient_email` VARCHAR(255) NOT NULL,
    `token` VARCHAR(100) NOT NULL UNIQUE,
    `expires_at` DATETIME(6) NOT NULL,
    `is_revoked` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `report_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_report_s_pre_cons_8b8cd9f2` FOREIGN KEY (`report_id`) REFERENCES `pre_consultation_reports` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_report_s_users_dad40958` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `safety_filter_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `user_id` BIGINT,
    `target_type` VARCHAR(50) NOT NULL,
    `target_id` VARCHAR(100),
    `blocked_reason` VARCHAR(100) NOT NULL,
    `original_text` LONGTEXT NOT NULL,
    `safe_replacement_text` LONGTEXT NOT NULL,
    `filter_stage` VARCHAR(30) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `model_improvement_datasets` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `dataset_version` VARCHAR(20) NOT NULL UNIQUE,
    `week_start` DATETIME(6) NOT NULL,
    `week_end` DATETIME(6) NOT NULL,
    `low_rated_guide_count` INT NOT NULL DEFAULT 0,
    `high_ocr_correction_count` INT NOT NULL DEFAULT 0,
    `thumbs_down_chat_count` INT NOT NULL DEFAULT 0,
    `total_records` INT NOT NULL DEFAULT 0,
    `consent_only` BOOL NOT NULL DEFAULT 1,
    `pseudonymized_at` DATETIME(6) NOT NULL,
    `pseudonymization_level` VARCHAR(200) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='REQ-FEED-002 — 주 1회 집계 결과 (가명처리 후 모델 개선 데이터셋).';
CREATE TABLE IF NOT EXISTS `model_versions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `model_name` VARCHAR(100) NOT NULL,
    `version` VARCHAR(20) NOT NULL,
    `description` LONGTEXT,
    `status` VARCHAR(20) NOT NULL COMMENT 'CANDIDATE: CANDIDATE\nDEPLOYED: DEPLOYED\nRETIRED: RETIRED' DEFAULT 'CANDIDATE',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_model_versi_model_n_8d5edb` (`model_name`, `version`)
) CHARACTER SET utf8mb4 COMMENT='REQ-FEED-002 — AI 모델 버저닝 이력.';
CREATE TABLE IF NOT EXISTS `prompt_versions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `prompt_type` VARCHAR(50) NOT NULL COMMENT 'HEALTH_GUIDE: HEALTH_GUIDE\nOCR_EXTRACT: OCR_EXTRACT\nOCR_STRUCTURE: OCR_STRUCTURE\nMEDICATION_INFO: MEDICATION_INFO',
    `version` VARCHAR(20) NOT NULL,
    `template_text` LONGTEXT NOT NULL,
    `improvement_reason` LONGTEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL COMMENT 'CANDIDATE: CANDIDATE\nAPPROVED: APPROVED\nREJECTED: REJECTED' DEFAULT 'CANDIDATE',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `source_dataset_id` CHAR(36),
    `source_prompt_id` CHAR(36),
    CONSTRAINT `fk_prompt_v_model_im_edb0e6ef` FOREIGN KEY (`source_dataset_id`) REFERENCES `model_improvement_datasets` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_prompt_v_prompts_4601ba87` FOREIGN KEY (`source_prompt_id`) REFERENCES `prompts` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COMMENT='REQ-FEED-002 — 프롬프트 개선 이력.';
CREATE TABLE IF NOT EXISTS `pill_recognitions` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `image_url` VARCHAR(512) NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `candidates` JSON,
    `selected_drug_name` VARCHAR(128),
    `user_confirmed` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_pill_rec_users_2e103417` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-PILL-001 / REQ-PILL-004 — 약품 이미지 인식 이력.';
CREATE TABLE IF NOT EXISTS `diet_infos` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `disease_code` VARCHAR(20) NOT NULL COMMENT 'RA: RA\nSLE: SLE\nDM1: DM1\nDM2: DM2\nHTN: HTN\nHYPERLIPIDEMIA: HYPERLIPIDEMIA\nASTHMA: ASTHMA\nCOPD: COPD\nPARKINSON: PARKINSON\nMS: MS\nBREAST_CANCER: BREAST_CANCER\nCOLON_CANCER: COLON_CANCER\nLUNG_CANCER: LUNG_CANCER',
    `category` VARCHAR(10) NOT NULL COMMENT 'RECOMMEND: RECOMMEND\nAVOID: AVOID',
    `food_category` VARCHAR(30),
    `food_name` VARCHAR(100) NOT NULL,
    `reason` LONGTEXT NOT NULL,
    `terms` JSON,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `content_conversions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `conversion_type` VARCHAR(20) NOT NULL COMMENT 'CARD: CARD\nTTS: TTS',
    `status` VARCHAR(20) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `file_url` VARCHAR(500),
    `file_urls` JSON,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `completed_at` DATETIME(6),
    `guide_id` INT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_content__health_g_46b5b166` FOREIGN KEY (`guide_id`) REFERENCES `health_guides` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_content__users_89ac2208` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `email_verify_codes` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `code` VARCHAR(6) NOT NULL,
    `expires_at` DOUBLE NOT NULL
) CHARACTER SET utf8mb4 COMMENT='인증코드 DB 저장 — 멀티워커/재시작 환경에서 인메모리 _store 대체';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)

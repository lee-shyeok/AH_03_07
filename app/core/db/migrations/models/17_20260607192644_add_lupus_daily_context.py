from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
        ALTER TABLE `users` ALTER COLUMN `mode` SET DEFAULT 'general';
        ALTER TABLE `users` MODIFY COLUMN `mode` VARCHAR(16) NOT NULL COMMENT 'GENERAL: general\nAUTOIMMUNE: autoimmune' DEFAULT 'general';
        ALTER TABLE `health_guides` MODIFY COLUMN `side_effect_monitoring` JSON NOT NULL;
        ALTER TABLE `health_guides` MODIFY COLUMN `sources` JSON NOT NULL;
        ALTER TABLE `audit_logs` MODIFY COLUMN `detail` JSON;
        ALTER TABLE `user_medications` ADD `end_date` DATE;
        ALTER TABLE `disease_activity_logs` MODIFY COLUMN `joint_swelling_areas` JSON;
        ALTER TABLE `symptom_check_logs` MODIFY COLUMN `checked_symptoms` JSON NOT NULL;
        ALTER TABLE `lupus_skin_logs` MODIFY COLUMN `symptom_type` VARCHAR(16) NOT NULL COMMENT 'RASH: RASH\nORAL_ULCER: ORAL_ULCER\nHAIR_LOSS: HAIR_LOSS\nRAYNAUD: RAYNAUD';
        ALTER TABLE `chat_messages` MODIFY COLUMN `rag_sources` JSON NOT NULL;
        ALTER TABLE `diary_symptom_logs` MODIFY COLUMN `feeling` JSON;
        ALTER TABLE `diary_symptom_logs` MODIFY COLUMN `body_parts` JSON;
        ALTER TABLE `emergency_cards` MODIFY COLUMN `emergency_contacts` JSON;
        ALTER TABLE `pharmacies` MODIFY COLUMN `operating_hours` JSON;
        ALTER TABLE `share_links` MODIFY COLUMN `categories` JSON NOT NULL;
        ALTER TABLE `prompts` MODIFY COLUMN `variables` JSON;
        ALTER TABLE `health_guide_contents` MODIFY COLUMN `metadata` JSON;
        ALTER TABLE `autoimmune_profiles` MODIFY COLUMN `vaccination_history` JSON NOT NULL;
        ALTER TABLE `autoimmune_profiles` MODIFY COLUMN `risk_factors` JSON NOT NULL;
        ALTER TABLE `auto_guides` MODIFY COLUMN `side_effect_monitoring` JSON NOT NULL;
        ALTER TABLE `auto_guides` MODIFY COLUMN `sources` JSON NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ALTER COLUMN `mode` SET DEFAULT 'GENERAL';
        ALTER TABLE `users` MODIFY COLUMN `mode` VARCHAR(16) NOT NULL COMMENT 'GENERAL: GENERAL\nAUTOIMMUNE: AUTOIMMUNE' DEFAULT 'GENERAL';
        ALTER TABLE `prompts` MODIFY COLUMN `variables` JSON;
        ALTER TABLE `audit_logs` MODIFY COLUMN `detail` JSON;
        ALTER TABLE `pharmacies` MODIFY COLUMN `operating_hours` JSON;
        ALTER TABLE `auto_guides` MODIFY COLUMN `side_effect_monitoring` JSON NOT NULL;
        ALTER TABLE `auto_guides` MODIFY COLUMN `sources` JSON NOT NULL;
        ALTER TABLE `share_links` MODIFY COLUMN `categories` JSON NOT NULL;
        ALTER TABLE `chat_messages` MODIFY COLUMN `rag_sources` JSON NOT NULL;
        ALTER TABLE `health_guides` MODIFY COLUMN `side_effect_monitoring` JSON NOT NULL;
        ALTER TABLE `health_guides` MODIFY COLUMN `sources` JSON NOT NULL;
        ALTER TABLE `lupus_skin_logs` MODIFY COLUMN `symptom_type` VARCHAR(16) NOT NULL COMMENT 'RASH: RASH\nORAL_ULCER: ORAL_ULCER\nHAIR_LOSS: HAIR_LOSS';
        ALTER TABLE `emergency_cards` MODIFY COLUMN `emergency_contacts` JSON;
        ALTER TABLE `user_medications` DROP COLUMN `end_date`;
        ALTER TABLE `diary_symptom_logs` MODIFY COLUMN `feeling` JSON;
        ALTER TABLE `diary_symptom_logs` MODIFY COLUMN `body_parts` JSON;
        ALTER TABLE `symptom_check_logs` MODIFY COLUMN `checked_symptoms` JSON NOT NULL;
        ALTER TABLE `autoimmune_profiles` MODIFY COLUMN `vaccination_history` JSON NOT NULL;
        ALTER TABLE `autoimmune_profiles` MODIFY COLUMN `risk_factors` JSON NOT NULL;
        ALTER TABLE `disease_activity_logs` MODIFY COLUMN `joint_swelling_areas` JSON;
        ALTER TABLE `health_guide_contents` MODIFY COLUMN `metadata` JSON;
        DROP TABLE IF EXISTS `lupus_daily_contexts`;"""


MODELS_STATE = (
    "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"
)

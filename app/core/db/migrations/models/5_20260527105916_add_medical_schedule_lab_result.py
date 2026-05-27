from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `medical_schedules` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `schedule_type` VARCHAR(16) NOT NULL COMMENT 'BLOOD_TEST: BLOOD_TEST\nURINE_TEST: URINE_TEST\nEYE_EXAM: EYE_EXAM\nAPPOINTMENT: APPOINTMENT\nINJECTION: INJECTION',
    `scheduled_date` DATE NOT NULL,
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_8614df87` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-004 — 자가면역 관리 의료 일정 (검사·진료·주사).';
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
) CHARACTER SET utf8mb4 COMMENT='REQ-LAB-001 — 사용자가 직접 입력한 검사 결과 (수동 입력·보관).';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `lab_results`;
        DROP TABLE IF EXISTS `medical_schedules`;"""


MODELS_STATE = (
    "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"
)

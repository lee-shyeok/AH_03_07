from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
) CHARACTER SET utf8mb4 COMMENT='REQ-ACTV-003 — 사용자가 직접 설정한 활성도 자가 모니터링 알림 기준 (사용자당 1개).';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `activity_alert_settings`;"""


MODELS_STATE = (
    "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"
)

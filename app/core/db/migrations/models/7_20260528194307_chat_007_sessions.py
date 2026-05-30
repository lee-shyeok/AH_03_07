from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `chat_messages`;
        DROP TABLE IF EXISTS `chat_sessions`;
        DROP TABLE IF EXISTS `chat_feedbacks`;"""


MODELS_STATE = (
    "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"
)

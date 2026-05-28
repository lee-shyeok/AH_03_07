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
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "RzqR07a7Uvp5FDLfBQMlq7FrjVf5p7+h+us7fW"
)

from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `user_diseases` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `disease_code` VARCHAR(16) NOT NULL COMMENT 'RA: RA\nSLE: SLE',
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
        ALTER TABLE `users` ADD `mode` VARCHAR(16) NOT NULL COMMENT 'GENERAL: GENERAL\nAUTOIMMUNE: AUTOIMMUNE' DEFAULT 'GENERAL';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` DROP COLUMN `mode`;
        DROP TABLE IF EXISTS `audit_logs`;
        DROP TABLE IF EXISTS `user_diseases`;"""


MODELS_STATE = (
    "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"
    "IhsXZVj4JqKHctVZrjrLVWdi1fn0P4DeH+Y="
)

from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_med_users_e877c4e6` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='REQ-AUTO-002 — 사용자가 등록한 자가면역 관련 약물.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_risk_profiles`;
        DROP TABLE IF EXISTS `user_medications`;"""


MODELS_STATE = (
    "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"
    "8HjaBgnA=="
)

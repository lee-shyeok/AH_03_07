from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `safety_filter_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY COMMENT '차단 이력 UUID',
    `user_id` BIGINT,
    `target_type` VARCHAR(50) NOT NULL COMMENT '차단 대상 유형 (CHAT, GUIDE, OCR 등)',
    `target_id` VARCHAR(100),
    `blocked_reason` VARCHAR(100) NOT NULL COMMENT '매칭된 카테고리 목록 (콤마 구분)',
    `original_text` LONGTEXT NOT NULL COMMENT '차단된 원본 텍스트',
    `safe_replacement_text` LONGTEXT NOT NULL COMMENT '대체 안전 문구',
    `filter_stage` VARCHAR(30) NOT NULL COMMENT '필터 적용 단계 (pre_generation, post_generation 등)',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='NFR-SAFE-003 — 의료행위 표현 차단 이력';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `safety_filter_logs`;"""

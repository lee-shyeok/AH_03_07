from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
) CHARACTER SET utf8mb4 COMMENT='REQ-SYMP-001 — 위험 증상 자가체크 기록. red_flag_triggered는 SYMP-002 룰 매칭 결과.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `disease_activity_logs`;
        DROP TABLE IF EXISTS `symptom_check_logs`;"""


MODELS_STATE = (
    "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"
    "1Cc0W4nDV/fSa0W9iVOKG6owivkJUy1PTdumUAI6S2ooTJVUq+tMr6RtVVS9Zh2k5im7mq"
    "e39TmpF/kiF5PONAM4B6vt4iWc2i18NG4PB52by0JwM8HsmzOD0cP9/bA9GjHtXSppgsml"
    "02t1W8MO/YBN9GmCrzqD7uCuc31ZWN9NcH/Uov/Cfg5R6Sm7mNIVsSldSZnSkaMi/CcUOC"
    "U89f2VGKnUMUlXdSmJS4FNSuJvsmOlq7p0VZdOQ9Jp6MydhjhfSeEoV/jfUhErWNZxsqnP"
    "ueyoZbke/7aLK040/pp5lM9q5KE8rRVYmrZ2yJlWNFaI74te13zvnLrmXyklrJSCmG6uL0"
    "6pNK2HJHHvnHpV5FCUx1ZwP6OxHsSkF/3A3OSHMqT251Tan02XcPckfJCjNGf/nWZCp34D"
    "HMWO+PDvCEnO1vqjHTg4Ay6aexyuEqIWoXiroJmWjcn/qY6LZjMMHUflfgVYCKGQ/o1+JO"
    "FPi5SsOt+hYVBYABEt9zr2S0QvY2YSUhX3sC+AjJWqE05EGqk/x9tJyMc80rc6J0itqdSa"
    "SuWa1Jq+kY7NqP+SVLZJZVvx9Mq25Fd3OZo2zod5xWo2/leBd9Oxjf7bu09qp9bxauxgwy"
    "ZVTJW0ckJvpWk06k0vXcQ1Th8LNpmDZwaYq6QL53NoU8XWVGlWC8E/KeyYhxlzS2pCqvuC"
    "F8zvSJuywmcCd6esVlT6RGVXK8YGBOnmYIDsJTXyaE91anS+RMb0wOKw+faIOl4B0hFHyk"
    "BnuFWWhmm5V5Z75cRe+ef/AWf34uo="
)

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `auto_guides` ADD COLUMN `deleted_at` DATETIME(6) NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `auto_guides` DROP COLUMN `deleted_at`;
    """

import sqlalchemy as sa
from ddcdatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.bot_models import EmbedPages


class EmbedPagesDal:
    def __init__(self, db_session, log):
        self.columns = list(EmbedPages.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_embed_pages(self, message_id: int, channel_id: int, author_id: int, pages: list[dict]):
        stmt = EmbedPages(
            message_id=message_id,
            channel_id=channel_id,
            author_id=author_id,
            pages=pages,
        )
        await self.db_utils.insert(stmt)

    async def get_embed_pages(self, message_id: int):
        stmt = select(*self.columns).where(EmbedPages.message_id == message_id)
        results = await self.db_utils.fetchall(stmt, True)
        return results[0] if results else None

    async def update_current_page(self, message_id: int, current_page: int):
        stmt = sa.update(EmbedPages).where(EmbedPages.message_id == message_id).values(current_page=current_page)
        await self.db_utils.execute(stmt)

    async def delete_embed_pages(self, message_id: int):
        stmt = sa.delete(EmbedPages).where(EmbedPages.message_id == message_id)
        await self.db_utils.execute(stmt)

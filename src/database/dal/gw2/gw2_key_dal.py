import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.gw2_models import Gw2Keys


class Gw2KeyDal:
    def __init__(self, db_session, log):
        self.columns = list(Gw2Keys.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_api_key(self, insert_args: dict):
        stmt = Gw2Keys(
            user_id=insert_args["user_id"],
            name=insert_args["key_name"],
            gw2_acc_name=insert_args["gw2_acc_name"],
            server=insert_args["server_name"],
            permissions=insert_args["permissions"],
            key=insert_args["api_key"],
        )
        await self.db_utils.insert(stmt)

    async def update_api_key(self, update_args: dict):
        stmt = (
            sa.update(Gw2Keys)
            .where(
                Gw2Keys.user_id == update_args["user_id"],
            )
            .values(
                name=update_args["key_name"],
                gw2_acc_name=update_args["gw2_acc_name"],
                server=update_args["server_name"],
                permissions=update_args["permissions"],
                key=update_args["api_key"],
            )
        )
        await self.db_utils.execute(stmt)

    async def delete_user_api_key(self, user_id: int):
        stmt = sa.delete(Gw2Keys).where(Gw2Keys.user_id == user_id)
        await self.db_utils.execute(stmt)

    async def get_api_key(self, api_key: str):
        stmt = select(*self.columns).where(
            Gw2Keys.key == api_key,
        )
        results = await self.db_utils.fetchall(stmt, True)
        return results

    async def get_api_key_by_name(self, key_name: str):
        stmt = select(*self.columns).where(Gw2Keys.name == key_name)
        results = await self.db_utils.fetchall(stmt, True)
        return results

    async def get_api_key_by_user(self, user_id: int):
        stmt = select(*self.columns).where(Gw2Keys.user_id == user_id)
        results = await self.db_utils.fetchall(stmt, True)
        return results

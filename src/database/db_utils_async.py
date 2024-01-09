# -*- coding: utf-8 -*-
from src.database.db_exceptions import (
    DBAddException,
    DBExecuteException,
    DBFetchAllException,
    DBFetchValueException
)


class DBUtilsAsync:
    def __init__(self, session, log):
        self.session = session
        self.log = log

    async def add(self, stmt):
        try:
            self.session.add(stmt)
        except Exception as e:
            self.session.rollback()
            raise DBAddException(self.log, e)
        else:
            await self.session.commit()

    async def execute(self, stmt):
        try:
            await self.session.execute(stmt)
        except Exception as e:
            self.session.rollback()
            raise DBExecuteException(self.log, e)
        else:
            await self.session.commit()

    async def fetchall(self, stmt):
        cursor = None
        try:
            cursor = await self.session.execute(stmt)
        except Exception as e:
            self.session.rollback()
            raise DBFetchAllException(self.log, e)
        else:
            await self.session.commit()
            return cursor.mappings().all()
        finally:
            cursor.close() if cursor is not None else None

    async def fetchone(self, stmt):
        cursor = None
        try:
            cursor = await self.session.execute(stmt)
        except Exception as e:
            self.session.rollback()
            raise DBFetchAllException(self.log, e)
        else:
            await self.session.commit()
            return cursor.mappings().first()
        finally:
            cursor.close() if cursor is not None else None

    async def fetch_value(self, stmt):
        cursor = None
        try:
            cursor = await self.session.execute(stmt)
        except Exception as e:
            self.session.rollback()
            raise DBFetchValueException(self.log, e)
        else:
            await self.session.commit()
            return cursor.first()[0]
        finally:
            cursor.close() if cursor is not None else None

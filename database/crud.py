from sqlalchemy.ext.asyncio import AsyncSession
from .models import SystemLoad, EventLog
from sqlalchemy.future import select
from datetime import datetime

async def save_load(cpu: float, gpu: float, memory: float, net_sent: float, net_recv: float, db: AsyncSession) -> None:
    """
    Сохраняет метрики системы в базу данных.
    """
    load = SystemLoad(
        cpu_percent=cpu,
        gpu_percent=gpu,
        memory_percent=memory,
        # сохраняем память
        net_sent=net_sent,
        net_recv=net_recv
    )
    db.add(load)
    await db.commit()

async def delete_old_system_loads(before_date: datetime, db: AsyncSession):
    stmt = select(SystemLoad).where(SystemLoad.timestamp < before_date)
    result = await db.execute(stmt)
    old_records = result.scalars().all()
    for record in old_records:
        await db.delete(record)
    await db.commit()

async def delete_old_events(before_date: datetime, db: AsyncSession):
    stmt = select(EventLog).where(EventLog.timestamp < before_date)
    result = await db.execute(stmt)
    old_records = result.scalars().all()
    for record in old_records:
        await db.delete(record)
    await db.commit()

async def get_last_loads(db: AsyncSession, limit: int = 10):
    """
    Возвращает последние записи метрик системы.
    """
    result = await db.execute(
        SystemLoad.__table__.select().order_by(SystemLoad.id.desc()).limit(limit)
    )
    return result.fetchall()

async def save_event(message: str, level: str, db: AsyncSession) -> None:
    """
    Сохраняет событие в журнал событий.
    """
    event = EventLog(message=message, level=level)
    db.add(event)
    await db.commit()

async def get_event_logs(db: AsyncSession, limit: int = 10):
    """
    Возвращает последние записи журнала событий.
    """
    result = await db.execute(
        EventLog.__table__.select().order_by(EventLog.id.desc()).limit(limit)
    )
    return result.fetchall()

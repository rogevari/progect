from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  
from pydantic import BaseModel
from services.monitor import SystemMonitor
from database.db import async_session
from database import crud
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
import io
import csv
from database.models import SystemLoad # модель с CPU, memory и т.п.

router = APIRouter()

async def get_db() -> AsyncSession:
    """
    Генератор сессии базы данных.
    """
    async with async_session() as session:
        yield session

@router.get("/api/load")
async def get_system_load(db: AsyncSession = Depends(get_db)):
    """
    Возвращает последние метрики системы.
    """
    data = await crud.get_last_loads(db)
    return [
        {
            "cpu": row.cpu_percent,
            "memory": row.memory_percent,
            "net_sent": row.net_sent,
            "net_recv": row.net_recv,
            "gpu_percent": SystemMonitor.get_gpu_load(),
            "timestamp": row.timestamp.isoformat()
        }
        for row in data
    ]


@router.get("/api/export")
async def export_data(
    start: str = Query(...),
    end: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Асинхронно экспортирует данные мониторинга в CSV за заданный период времени.
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return {"error": "Invalid datetime format. Use ISO 8601 (e.g. 2025-04-15T10:00:00)."}


    stmt = select(SystemLoad).where(SystemLoad.timestamp.between(start_dt, end_dt))
    result = await db.execute(stmt)
    rows = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "cpu_percent", "gpu_percent", "memory_percent", "net_sent", "net_recv"])

    for row in rows:
        writer.writerow([
            row.timestamp.isoformat(),
            row.cpu_percent,
            row.gpu_percent,
            row.memory_percent,
            row.net_sent,
            row.net_recv
        ])

    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=export.csv"})



@router.get("/api/events")
async def get_events(db: AsyncSession = Depends(get_db)):
    """
    Возвращает последние записи журнала событий.
    """
    events = await crud.get_event_logs(db)
    return [
        {
            "message": event.message,
            "level": event.level,
            "timestamp": event.timestamp.isoformat()
        }
        for event in events
    ]

class Thresholds(BaseModel):
    """
    Pydantic-модель для передачи пороговых значений.
    """
    cpu: float
    gpu: float
    memory: float      # новое поле для памяти
    net_sent: float
    net_recv: float


@router.get("/api/thresholds", response_model=Thresholds)
async def get_thresholds(request: Request):
    """
    Возвращает текущие пороговые значения.
    """
    return request.app.state.thresholds

@router.post("/api/thresholds", response_model=Thresholds)
async def update_thresholds(thresholds: Thresholds, request: Request):
    """
    Обновляет пороговые значения.
    """
    request.app.state.thresholds = thresholds.dict()
    return request.app.state.thresholds

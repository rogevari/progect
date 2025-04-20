import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from services.monitor import SystemMonitor
from database import crud, db
from database.db import engine, Base
from api.routes import router as api_router
from datetime import datetime, timedelta

app = FastAPI()
app.include_router(api_router)
templates = Jinja2Templates(directory="templates")

# Пороговые значения для уведомлений (по умолчанию)
THRESHOLDS = {
    "cpu": 90.0,                   
    "gpu": 90.0,                   
    "memory": 90.0,                
    "net_sent": 10 * 1024 * 1024,  
    "net_recv": 10 * 1024 * 1024   
}

# Сохраняем пороговые значения в состоянии приложения
app.state.thresholds = THRESHOLDS

async def init_db():
    """
    Инициализация базы данных. Создает таблицы только если их нет.
    """
    async with engine.begin() as connection:
        # Только если таблицы еще не созданы, они будут созданы
        await connection.run_sync(Base.metadata.create_all)

async def delete_old_records():
    """
    Удаляет записи старше 5 дней.
    """
    async with db.async_session() as session:
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        await crud.delete_old_system_loads(five_days_ago, session)
        await crud.delete_old_events(five_days_ago, session)

@app.on_event("startup")
async def startup_event():
    """
    Событие старта приложения:
    1. Инициализация базы данных.
    2. Запуск фоновых задач по логированию метрик и очистке старых данных.
    """
    await init_db()  # Инициализация базы данных, но не её переинициализация.

    last_net_sent, last_net_recv = SystemMonitor.get_network_counters()

    # Периодически удаляем старые записи
    async def cleanup_task():
        while True:
            await delete_old_records()  # Очистка старых записей раз в сутки
            await asyncio.sleep(86400)  # Очистка раз в сутки (86400 секунд)

    asyncio.create_task(cleanup_task())  # Запуск задачи очистки данных

    # Функция для логирования метрик
    async def log_metrics():
        nonlocal last_net_sent, last_net_recv
        while True:
            cpu = SystemMonitor.get_cpu_load()
            gpu = SystemMonitor.get_gpu_load()   # Получение загрузки GPU
            memory = SystemMonitor.get_memory_load()  # Получение загрузки памяти
            current_net_sent, current_net_recv = SystemMonitor.get_network_counters()

            net_sent_speed = (current_net_sent - last_net_sent) / 2
            net_recv_speed = (current_net_recv - last_net_recv) / 2
            last_net_sent, last_net_recv = current_net_sent, current_net_recv

            async with db.async_session() as session:
                # Передаём все метрики: CPU, GPU, Memory, Net Sent, Net Recv
                await crud.save_load(cpu, gpu, memory, net_sent_speed, net_recv_speed, session)

                thresholds = app.state.thresholds
                if cpu > thresholds["cpu"]:
                    await crud.save_event(
                        message=f"Критическая загрузка CPU: {cpu}%",
                        level="CRITICAL",
                        db=session
                    )
                if gpu > thresholds["gpu"]:
                    await crud.save_event(
                        message=f"Критическая загрузка GPU: {gpu}%",
                        level="CRITICAL",
                        db=session
                    )
                if memory > thresholds["memory"]:
                    await crud.save_event(
                        message=f"Критическая загрузка памяти: {memory}%",
                        level="CRITICAL",
                        db=session
                    )
                if net_sent_speed > thresholds["net_sent"]:
                    await crud.save_event(
                        message=f"Высокая скорость исходящего трафика: {net_sent_speed:.2f} B/s",
                        level="CRITICAL",
                        db=session
                    )
                if net_recv_speed > thresholds["net_recv"]:
                    await crud.save_event(
                        message=f"Высокая скорость входящего трафика: {net_recv_speed:.2f} B/s",
                        level="CRITICAL",
                        db=session
                    )
            await asyncio.sleep(2)

    # Запуск фоновой задачи логирования метрик
    asyncio.create_task(log_metrics())

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Отображает главную страницу с графиками и формой настройки порогов.
    """
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

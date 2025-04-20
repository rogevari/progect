from sqlalchemy import Column, Integer, Float, DateTime, String, func
from .db import Base

class SystemLoad(Base):
    """
    Модель для хранения метрик системы:
      cpu_percent       - загрузка CPU (%),
      gpu_percent       - загрузка GPU (%),
      memory_percent    - загрузка памяти (%),
      net_sent          - скорость исходящего трафика (B/s),
      net_recv          - скорость входящего трафика (B/s),
      timestamp         - время записи метрик.
    """
    __tablename__ = "system_load"

    id = Column(Integer, primary_key=True, index=True)
    cpu_percent = Column(Float, nullable=False)
    gpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=False)
    net_sent = Column(Float, nullable=True)
    net_recv = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class EventLog(Base):
    """
    Модель для хранения событий:
      message   - текст уведомления,
      level     - уровень уведомления (например, CRITICAL),
      timestamp - время события.
    """
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    level = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

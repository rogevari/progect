import psutil
import GPUtil

class SystemMonitor:
    """
    Сервис для получения текущих метрик системы.
    """

    @staticmethod
    def get_cpu_load() -> float:
        """
        Возвращает текущую загрузку CPU в процентах.
        """
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def get_gpu_load() -> float:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].load * 100
            return 0.0
        except Exception:
            return 0.0


    @staticmethod
    def get_memory_load() -> float:
        """
        Возвращает текущую загрузку памяти в процентах.
        """
        return psutil.virtual_memory().percent

    @staticmethod
    def get_network_counters() -> tuple:
        """
        Возвращает текущие сетевые счетчики: (bytes_sent, bytes_recv).
        """
        counters = psutil.net_io_counters()
        return counters.bytes_sent, counters.bytes_recv

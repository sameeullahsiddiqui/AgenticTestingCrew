from ansi2html import Ansi2HTMLConverter
from backend.helpers.socket_manager import SocketManager
import logging

class WebSocketLogHandler(logging.Handler):
    def __init__(self, socket_manager: SocketManager, source: str = "CrewAI"):
        super().__init__()
        self.socket_manager = socket_manager
        self.source = source
        self.ansi_converter = Ansi2HTMLConverter(inline=True)

    def emit(self, record):
        log_entry = self.format(record)
        html_log = self.ansi_converter.convert(log_entry, full=False)
        if self.socket_manager:
            import asyncio
            asyncio.create_task(self.socket_manager.broadcast({
                "type": "log",
                "source": self.source,
                "message": html_log 
            }))

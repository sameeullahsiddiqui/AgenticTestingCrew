import logging
import asyncio
import logging
import asyncio
from ansi2html import Ansi2HTMLConverter
from backend.helpers.socket_manager import SocketManager

class WebSocketLogHandler(logging.Handler):
    def __init__(self, socket_manager: SocketManager, source: str = "CrewAI"):
        super().__init__()
        self.socket_manager = socket_manager
        self.source = source
        self.ansi_converter = Ansi2HTMLConverter(inline=True)

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)
            html_log = self.ansi_converter.convert(log_entry, full=False)

            message = {
                "type": "log",
                "source": self.source,
                "message": html_log
            }

            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.socket_manager.broadcast(message))
            else:
                asyncio.run(self.socket_manager.broadcast(message))

        except Exception as e:
            # Avoid recursive logging errors
            print(f"Logging error: {e}")

# backend/helpers/stdout_redirector.py
import sys
import asyncio
from io import StringIO

class StdoutCapture:
    def __init__(self, socket_manager=None, source="CrewAI"):
        self.original_stdout = sys.stdout
        self.buffer = StringIO()
        self.socket_manager = socket_manager
        self.source = source

    def write(self, message):
        self.original_stdout.write(message)
        self.buffer.write(message)

        if self.socket_manager and message.strip():
            # Send each line separately if it's a multi-line string
            asyncio.create_task(
                self.socket_manager.broadcast(
                    message.strip(),
                    source=self.source
                )
            )

    def flush(self):
        self.original_stdout.flush()
        self.buffer.flush()

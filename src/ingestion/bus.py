import asyncio
import queue
import time
from typing import Optional, Callable, Awaitable
from src.ingestion.schemas import UnifiedInputPacket

class StreamBus:
    """
    Production-grade, thread-safe Frame Buffer.
    Implements a LIFO drop policy on overflow to prioritize real-time motion capture.
    """
    def __init__(self, maxsize: int = 500):
        self.queue = queue.Queue(maxsize=maxsize)
        self.total_dropped = 0

    def push(self, packet: UnifiedInputPacket):
        """
        Pushes a packet into the bus. Drops the oldest frame if full (LIFO-like behavior for real-time).
        """
        try:
            if self.queue.full():
                # Drop the oldest frame to make space for the newest (Real-time priority)
                try:
                    self.queue.get_nowait()
                    self.total_dropped += 1
                except queue.Empty:
                    pass
            
            self.queue.put_nowait(packet)
        except Exception as e:
            print(f"[StreamBus Error] Failed to push packet: {e}")

    async def consume(self, callback: Callable[[UnifiedInputPacket], Awaitable[None]]):
        """
        Async consumer loop. Dispatches packets from the queue to the next pipeline stage.
        """
        print(f"[StreamBus] Consumer started...")
        while True:
            try:
                # Use a small timeout to remain responsive to shutdown signals
                if not self.queue.empty():
                    packet = self.queue.get_nowait()
                    await callback(packet)
                else:
                    await asyncio.sleep(0.005) # 5ms throttle
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"[StreamBus Consumer Error] {e}")
                await asyncio.sleep(0.1)

    def qsize(self) -> int:
        return self.queue.qsize()

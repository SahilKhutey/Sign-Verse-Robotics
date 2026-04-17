import websocket
import json
import threading
from typing import Dict, Any, Callable

class UnityBridge:
    """
    Real-Time WebSocket Bridge for Unity Digital Twin.
    Synchronizes virtual sensors and robotic joint actions.
    """
    def __init__(self, url: str = "ws://localhost:8080/signverse"):
        self.url = url
        self.ws = None
        self.on_observation_received: Optional[Callable] = None
        self.is_connected = False

    def connect(self):
        """Initializes the persistent connection to Unity."""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        # Run in background thread
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

    def send_action(self, action: Dict[str, Any]):
        """Sends agent command to the virtual robot in Unity."""
        if self.is_connected:
            payload = json.dumps({
                "type": "ROBOT_ACTION",
                "data": action
            })
            self.ws.send(payload)

    def _on_message(self, ws, message):
        """Handles incoming virtual sensor data from Unity."""
        data = json.loads(message)
        if self.on_observation_received:
            self.on_observation_received(data)

    def _on_open(self, ws):
        print(f"📡 Unity Digital Twin connected at {self.url}")
        self.is_connected = True

    def _on_close(self, ws, close_status_code, close_msg):
        print("📡 Unity connection closed.")
        self.is_connected = False

    def _on_error(self, ws, error):
        print(f"📡 Unity Bridge Error: {error}")

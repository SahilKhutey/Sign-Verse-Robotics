"""
Sign-Verse NVIDIA Isaac Sim Connector (UDP)
Usage: Run this script inside the Isaac Sim script editor or as a standalone Omniverse extension.
It listens for UDP packets from the Sign-Verse Orchestrator and actuates a specified robot.
"""

import socket
import json
import asyncio

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
ROBOT_PRIM_PATH = "/World/Robot" # Adjust this to your robot's path in Isaac Sim

def receive_telemetry():
    """
    Standard Python Receiver for Sign-Verse Telemetry.
    Can be integrated into an OmniGraph node or a standard Python action script.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)
    
    print(f"Sign-Verse Connector: Listening on {UDP_IP}:{UDP_PORT}...")
    
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            joint_data = json.loads(data.decode('utf-8'))
            
            # Example: Applying joints to a robot in Isaac Sim
            # In Isaac Sim, you would typically use:
            # from omni.isaac.core.robots import Robot
            # my_robot = Robot(ROBOT_PRIM_PATH)
            # my_robot.set_joint_positions(joint_data_values)
            
            print(f"Received Sync: {len(joint_data)} joints updated.")
            
        except BlockingIOError:
            # No data this frame
            pass
        except Exception as e:
            print(f"Sync Error: {e}")

if __name__ == "__main__":
    receive_telemetry()

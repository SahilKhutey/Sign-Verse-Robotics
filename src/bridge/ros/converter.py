import time
from typing import Dict, Any, Optional
from src.motion.core.state import MotionState

class ROSConverter:
    """
    Standard Logic for converting Sign-Verse MotionState (S_t) into 
    Robotic Operating System (ROS2) message formats.
    """
    def to_ros_msg_dict(self, motion_state: MotionState) -> Dict[str, Any]:
        """
        Generates a dictionary representation compatible with ROS2 message constructors.
        Targeting: geometry_msgs/Pose, geometry_msgs/Twist, std_msgs/Header
        """
        
        # 1. Pose: Position of the body centroid
        pose = {
            "position": {
                "x": float(motion_state.position[0]),
                "y": float(motion_state.position[1]),
                "z": float(motion_state.position[2])
            },
            "orientation": {
                "x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0 # Placeholder for rotation
            }
        }
        
        # 2. Twist: Linear velocity of the body
        twist = {
            "linear": {
                "x": float(motion_state.velocity[0]),
                "y": float(motion_state.velocity[1]),
                "z": float(motion_state.velocity[2])
            },
            "angular": {
                "x": 0.0, "y": 0.0, "z": 0.0
            }
        }
        
        # 3. Header: Synchronization
        header = {
            "stamp": {
                "sec": int(motion_state.timestamp),
                "nanosec": int((motion_state.timestamp % 1) * 1e9)
            },
            "frame_id": "world"
        }
        
        return {
            "header": header,
            "pose": pose,
            "twist": twist,
            "confidence": motion_state.confidence,
            "source": motion_state.source_id
        }

    def to_joint_state(self, motion_state: MotionState) -> Optional[Dict[str, Any]]:
        """
        Future: Converts skeletal joints to sensor_msgs/JointState.
        Currently returns the raw joint array as a dictionary list.
        """
        if motion_state.joints is None:
            return None
            
        return {
            "positions": motion_state.joints.tolist(),
            "name": [f"joint_{i}" for i in range(len(motion_state.joints))]
        }

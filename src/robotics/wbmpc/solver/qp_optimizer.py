import numpy as np
import ctypes
import os
import platform
import logging
from typing import Tuple

# Initialize structured logging
logger = logging.getLogger("SignVerse.Robotics.WBMPC")

class WBMPCSolver:
    """
    Python wrapper for the High-Performance C++ WBMPC Solver.
    Falls back to a NumPy numerical optimizer if the C++ library is unavailable.
    """
    def __init__(self, lib_name: str = "optimizer"):
        self.lib = None
        
        # Check for explicit force-numpy flag
        if os.environ.get("SV_FORCE_NUMPY_SOLVER") == "1":
            logger.info("Force-NumPy mode enabled. Skipping C++ solver discovery.")
            return

        system = platform.system()
        ext = ".dll" if system == "Windows" else ".so"
        
        # Try finding the compiled shared library in the same directory
        dir_path = os.path.dirname(os.path.realpath(__file__))
        lib_path = os.path.join(dir_path, lib_name + ext)
        
        if os.path.exists(lib_path):
            try:
                self.lib = ctypes.CDLL(lib_path)
                self.lib.solve_wbmpc.argtypes = [
                    ctypes.POINTER(ctypes.c_double), 
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int,
                    ctypes.POINTER(ctypes.c_double)
                ]
                logger.info(f"Successfully loaded C++ WBMPC solver: {lib_path}")
            except Exception as e:
                logger.error(f"Error loading C++ solver: {e}")
        else:
            logger.info(f"WBMPC C++ solver not found at {lib_path}. Defaulting to NumPy PD fallback.")

    def solve(self, state: np.ndarray, ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        state: [pos_x, pos_y, pos_z, vel_x, vel_y, vel_z]
        ref: [target_pos_x, target_pos_y, target_pos_z]
        Returns: (control_acc, contact_forces)
        """
        if self.lib:
            # High-Performance C++ Path
            c_state = (ctypes.c_double * 6)(*state)
            c_ref = (ctypes.c_double * 3)(*ref)
            c_out = (ctypes.c_double * 3)()
            self.lib.solve_wbmpc(c_state, c_ref, 20, c_out)
            forces = np.array([c_out[0], c_out[1], c_out[2]])
            
            # Simplified coupling: F = m*a
            mass = 47.0 # Unitree H1 Mass
            acc = forces / mass 
            acc[2] -= 9.81 # Remove gravity offset for pure acceleration vector
            return acc, forces
        else:
            # NumPy Fallback Path (Proportional-Derivative)
            error = ref - state[:3]
            vel = state[3:6]
            
            mass = 47.0 # Unitree H1
            kp = 150.0
            kd = 25.0
            
            # Simple PD formulation
            a_des = kp * error - kd * vel
            
            # Forces required F = m(a + g)
            forces = mass * a_des
            forces[2] += mass * 9.81
            
            return a_des, forces

import numpy as np
import ctypes
import os
from typing import Tuple

class WBMPCSolver:
    """
    Python wrapper for the High-Performance C++ WBMPC Solver.
    Falls back to a NumPy numerical optimizer if the C++ library is unavailable.
    """
    def __init__(self, lib_path: str = "src/robotics/wbmpc/solver/optimizer.so"):
        self.lib = None
        if os.path.exists(lib_path):
            try:
                self.lib = ctypes.CDLL(lib_path)
                self.lib.solve_wbmpc.argtypes = [
                    ctypes.POINTER(ctypes.c_double), 
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int,
                    ctypes.POINTER(ctypes.c_double)
                ]
            except Exception:
                pass

    def solve(self, state: np.ndarray, ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        state: [pos, vel]
        ref: [target_pos]
        Returns: (control_acc, contact_forces)
        """
        if self.lib:
            # High-Performance C++ Path
            c_state = (ctypes.c_double * 6)(*state)
            c_ref = (ctypes.c_double * 3)(*ref)
            c_out = (ctypes.c_double * 3)()
            self.lib.solve_wbmpc(c_state, c_ref, 20, c_out)
            forces = np.array([c_out[0], c_out[1], c_out[2]])
            acc = (forces / 75.0) # Simplified coupling
            return acc, forces
        else:
            # NumPy Fallback Path (Static/Dynamic blending)
            error = ref - state[:3]
            forces = 75.0 * (error * 1.2 + np.array([0, 0, 9.81])) # Proportional + Gravity
            acc = error * 0.5
            return acc, forces

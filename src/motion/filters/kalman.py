import numpy as np

class KalmanFilter:
    """
    Standard Linear Kalman Filter for 3D position and velocity tracking.
    State Vector: [x, y, z, vx, vy, vz]
    """
    def __init__(self, dt: float = 1/30.0):
        self.dt = dt

        # State Transition Matrix F: x_new = x + v*dt
        self.F = np.array([
            [1, 0, 0, dt, 0, 0],
            [0, 1, 0, 0, dt, 0],
            [0, 0, 1, 0, 0, dt],
            [0, 0, 0, 1,  0, 0],
            [0, 0, 0, 0,  1, 0],
            [0, 0, 0, 0,  0, 1],
        ], dtype=np.float32)

        # Measurement Matrix H: We only measure position [x, y, z]
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ], dtype=np.float32)

        # Process Noise Covariance Q
        self.Q = np.eye(6, dtype=np.float32) * 0.01

        # Measurement Noise Covariance R
        self.R = np.eye(3, dtype=np.float32) * 0.1

        # Initial State Estimate
        self.x = np.zeros((6, 1), dtype=np.float32)
        
        # Initial Covariance Estimate
        self.P = np.eye(6, dtype=np.float32)

    def predict(self) -> np.ndarray:
        """
        Prediction phase: Project state and covariance ahead.
        """
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """
        Update phase: Incorporate new measurement z = [x, y, z]^T.
        """
        z = measurement.reshape(3, 1)

        # Innovation (error)
        y = z - self.H @ self.x
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Optimal Kalman Gain
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update state and covariance
        self.x = self.x + K @ y
        self.P = (np.eye(6, dtype=np.float32) - K @ self.H) @ self.P

        return self.x

    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (position, velocity) as (3,) vectors."""
        return self.x[:3].flatten(), self.x[3:].flatten()

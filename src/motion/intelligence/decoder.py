import numpy as np

class IntentDecoder:
    """
    Decodes motion embeddings into high-level human intents.
    Initial version: Rule-based / Fingerprint matching.
    Scale version: Transformer / LSTM Classifier.
    """
    def decode(self, embedding: np.ndarray) -> str:
        """
        Interprets the motion vector.
        Simplified logic: use vector magnitude and specific spatial heuristics.
        """
        if embedding.size == 0:
            return "IDLE"

        # Heuristic: High activity in upper torso region usually implies a greeting or command
        activity_mag = np.mean(np.abs(embedding))

        if activity_mag > 0.4:
            return "GREETING/WAVE"
        elif activity_mag > 0.2:
            return "GESTURE_IN_PROGRESS"
        
        return "IDLE"

    def get_confidence(self, embedding: np.ndarray) -> float:
        """Heuristic confidence score for the decoded intent."""
        return float(np.clip(np.mean(np.abs(embedding)), 0.0, 1.0))

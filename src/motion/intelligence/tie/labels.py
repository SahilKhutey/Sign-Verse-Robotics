from typing import Dict, List

class IntentLabels:
    """
    TIE v2 Gesture Vocabulary.
    Maps human intents to neural network indices.
    """
    MAP = {
        0: "IDLE",
        1: "GREETING",
        2: "POINTING",
        3: "STOP",
        4: "WAVE",
        5: "THANK_YOU",
        6: "DISENGAGE"
    }
    
    INV_MAP = {v: k for k, v in MAP.items()}
    
    @classmethod
    def get_count(cls) -> int:
        return len(cls.MAP)
        
    @classmethod
    def get_name(cls, idx: int) -> str:
        return cls.MAP.get(idx, "UNKNOWN")
        
    @classmethod
    def get_idx(cls, name: str) -> int:
        return cls.INV_MAP.get(name, 0)

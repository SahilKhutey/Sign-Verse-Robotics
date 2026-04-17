import torch

class UncertaintyEstimator:
    """
    Measures neural model confusion using Shannon Entropy.
    Determines if the MMTE results are reliable or should be ignored for safety.
    """
    def __init__(self, entropy_threshold: float = 1.6):
        self.threshold = entropy_threshold

    def compute_entropy(self, probs: torch.Tensor) -> float:
        """
        Calculates the entropy of a probability distribution.
        H(x) = -sum(p(x) * log(p(x)))
        """
        # Ensure we avoid log(0)
        return -torch.sum(probs * torch.log(probs + 1e-8)).item()

    def is_uncertain(self, probs: torch.Tensor) -> bool:
        """
        Returns True if the model is too 'confused' to make a stable decision.
        """
        return self.compute_entropy(probs) > self.threshold

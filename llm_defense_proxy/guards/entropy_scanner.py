import collections
from scipy.stats import entropy
from typing import Dict, Any, Tuple, List

class EntropyScanner:
    def __init__(self, char_entropy_threshold: float = 4.4, word_length_threshold: int = 25):
        self.char_entropy_threshold = char_entropy_threshold
        self.word_length_threshold = word_length_threshold

    def calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        counts = collections.Counter(text)
        probabilities = [count / len(text) for count in counts.values()]
        return float(entropy(probabilities, base=2))

    def scan(self, text: str) -> Dict[str, Any]:
        tokens = text.split()
        flagged_tokens = []

        for token in tokens:
            if len(token) >= self.word_length_threshold:
                score = self.calculate_entropy(token)
                if score >= self.char_entropy_threshold:
                    flagged_tokens.append({"token": token, "entropy": round(score, 3)})

        overall_entropy = self.calculate_entropy(text)
        is_blocked = len(flagged_tokens) > 0

        return {
            "passed": not is_blocked,
            "overall_entropy": round(overall_entropy, 3),
            "flagged_tokens": flagged_tokens,
            "reason": "High entropy obfuscation detected (potential cipher/base64 payload)" if is_blocked else None
        }

    def check(self, text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Compatibility wrapper for main.py calling check()"""
        result = self.scan(text)
        return result["passed"], result["reason"], result["flagged_tokens"]
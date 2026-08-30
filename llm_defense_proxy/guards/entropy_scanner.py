import base64
import collections
import re
from scipy.stats import entropy
from typing import Dict, Any, Tuple, List

class EntropyScanner:
    def __init__(self, char_entropy_threshold: float = 4.4, word_length_threshold: int = 20):
        self.char_entropy_threshold = char_entropy_threshold
        self.word_length_threshold = word_length_threshold

    def calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        counts = collections.Counter(text)
        probabilities = [count / len(text) for count in counts.values()]
        return float(entropy(probabilities, base=2))

    def _is_valid_base64(self, s: str) -> Tuple[bool, str]:
        """Check if string is valid base64 and returns decoded string if valid."""
        clean_s = s.strip()
        if len(clean_s) < 16 or len(clean_s) % 4 != 0:
            return False, ""
        if not re.match(r"^[A-Za-z0-9+/=]+$", clean_s):
            return False, ""
        try:
            decoded_bytes = base64.b64decode(clean_s, validate=True)
            decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
            # Require decoded string to contain readable text
            if len(decoded_str) > 5 and any(c.isalpha() for c in decoded_str):
                return True, decoded_str
        except Exception:
            pass
        return False, ""

    def scan(self, text: str) -> Dict[str, Any]:
        tokens = text.split()
        flagged_tokens = []
        base64_detected = False
        decoded_payloads = []

        # Check for explicit base64 directives or keywords
        if re.search(r"(?i)(encoded\s+in\s+base64|base64\s+decode|decode\s+and\s+execute)", text):
            base64_detected = True

        for token in tokens:
            # Strip common punctuation around token
            clean_token = token.strip(".,;:\"'()[]{}<>")
            
            # Check base64 validity
            is_b64, decoded_text = self._is_valid_base64(clean_token)
            if is_b64:
                base64_detected = True
                decoded_payloads.append(decoded_text)

            if len(clean_token) >= self.word_length_threshold:
                score = self.calculate_entropy(clean_token)
                if score >= self.char_entropy_threshold or is_b64:
                    flagged_tokens.append({"token": clean_token, "entropy": round(score, 3)})

        overall_entropy = self.calculate_entropy(text)
        is_blocked = (len(flagged_tokens) > 0) or base64_detected

        reason = None
        if is_blocked:
            if base64_detected:
                reason = "Obfuscation / Base64: Base64 encoded payload detected"
            else:
                reason = "High entropy obfuscation detected (potential cipher/base64 payload)"

        return {
            "passed": not is_blocked,
            "overall_entropy": round(overall_entropy, 3),
            "flagged_tokens": flagged_tokens,
            "decoded_payloads": decoded_payloads,
            "reason": reason
        }

    def check(self, text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Compatibility wrapper for main.py calling check()"""
        result = self.scan(text)
        return result["passed"], result["reason"], result["flagged_tokens"]
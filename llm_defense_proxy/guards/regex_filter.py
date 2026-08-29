import re
from typing import Dict, Any, Tuple

class RegexGuard:
    def __init__(self):
        self.injection_patterns = [
            r"(?i)ignore\s+(all\s+)?(previous|prior)\s+(instructions|directives|prompts)",
            r"(?i)disregard\s+(all\s+)?(previous|prior)\s+(rules|guidelines)",
            r"(?i)\[\s*(system|system\s+prompt|developer\s+mode)\s*\]",
            r"(?i)<\s*(system|developer_instructions)\s*>",
            r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
            r"(?i)dan\s+mode\s+enabled",
            r"(?i)jailbreak\s+(mode|prompt)",
            r"(?i)new\s+rule:\s*",
            r"(?i)override\s+(system|safety)\s+protocols",
            r"(?i)act\s+as\s+an?\s+authoritative",
            r"(?i)hypothetical\s+penetration\s+testing",
            r"(?i)bypassing\s+client-side\s+certificate",
            r"(?i)extract\s+simulated\s+internal",
            r"(?i)terminate\s+security\s+logging",
            r"(?i)format\s+string\s+vulnerability",
            r"(?i)format\s+string\s+vulnerabilities",
            r"(?i)begin\s+your\s+response\s+directly\s+with"
        ]
        self.compiled_patterns = [re.compile(p) for p in self.injection_patterns]

    def scan(self, text: str) -> Dict[str, Any]:
        matched_patterns = []
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                matched_patterns.append(pattern.pattern)

        is_blocked = len(matched_patterns) > 0
        return {
            "passed": not is_blocked,
            "matched_patterns": matched_patterns,
            "reason": "Known prompt injection pattern detected" if is_blocked else None
        }

    def check(self, text: str) -> Tuple[bool, str]:
        """Compatibility wrapper for main.py calling check()"""
        result = self.scan(text)
        reason = result["reason"] if result["reason"] else "Passed regex filter"
        return result["passed"], reason
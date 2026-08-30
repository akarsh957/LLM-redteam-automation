import re

class OutputSanitizer:
    def __init__(self):
        # Define patterns or sensitive keywords to scrub from LLM outputs
        self.sensitive_patterns = [
            r"(?i)api[_-]?key\s*[:=]\s*['\"]?\w+['\"]?",
            r"(?i)secret[_-]?token\s*[:=]\s*['\"]?\w+['\"]?",
            r"(?i)password\s*[:=]\s*['\"]?\w+['\"]?",
            r"(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
            r"(?i)-----BEGIN\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+PRIVATE\s+KEY-----",
        ]
        self.compiled_patterns = [re.compile(p) for p in self.sensitive_patterns]

    def sanitize(self, text: str) -> tuple[str, bool]:
        """
        Scans and cleans the upstream LLM response text.
        Returns: (cleaned_text: str, sanitizer_triggered: bool)
        """
        if not text:
            return text, False

        triggered = False
        cleaned_text = text

        for pattern in self.compiled_patterns:
            if pattern.search(cleaned_text):
                triggered = True
                cleaned_text = pattern.sub("[REDACTED]", cleaned_text)

        return cleaned_text, triggered
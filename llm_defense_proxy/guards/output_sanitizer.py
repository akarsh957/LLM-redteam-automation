class OutputSanitizer:
    def __init__(self):
        # Define patterns or sensitive keywords you want to scrub from LLM outputs
        self.sensitive_keywords = [
            "password",
            "api_key",
            "secret_token"
        ]

    def sanitize(self, text: str) -> tuple[str, bool]:
        """
        Scans and cleans the upstream LLM response text.
        Returns: (cleaned_text: str, sanitizer_triggered: bool)
        """
        if not text:
            return text, False

        triggered = False
        cleaned_text = text

        # Simple redaction logic example
        for keyword in self.sensitive_keywords:
            if keyword in cleaned_text.lower():
                triggered = True
                # Redact or mask the sensitive term
                cleaned_text = cleaned_text.replace(keyword, "[REDACTED]")

        return cleaned_text, triggered
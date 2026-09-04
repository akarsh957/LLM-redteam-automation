import os
import re
from typing import Dict, Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency may be unavailable in local/offline installs.
    Groq = None


class LlamaGuardScanner:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key and Groq is not None else None
        self.model_id = "llama-guard-3-8b"
        
        # Standard MLCommons Taxonomy mapping used by Llama Guard 3
        self.category_map = {
            "S1": "Violent Crimes",
            "S2": "Non-Violent Crimes",
            "S3": "Sex-Related Crimes",
            "S4": "Child Exploitation",
            "S5": "Defamation",
            "S6": "Specialized Advice",
            "S7": "Privacy / PII",
            "S8": "Intellectual Property",
            "S9": "Indiscriminate Weapons",
            "S10": "Hate Speech",
            "S11": "Suicide / Self-Harm",
            "S12": "Sexual Content",
            "S13": "Cyberattacks / Malicious Software"
        }

        # Fallback taxonomy rules for offline / keyless intent scanning
        self.fallback_taxonomy = [
            (r"(?i)(bypassing\s+client-side|certificate\s+validation|memory\s+registers|format\s+string\s+vulnerabilit|terminate\s+security\s+logging|bash\s+one-liner|buffer\s+overflow|sql\s+injection|malware|exploit|keylogger|ransomware|hack\s+into|hacking|crack\s+passwords|virus|hijack)", "Cyberattacks / Malicious Software"),
            (r"(?i)(environment\s+configuration\s+variables|system\s+memory|exfiltrate|secret_key|api_key|private\s+key|credentials|credit\s+card|cvv|social\s+security|ssn|leaked\s+card|passport\s+number|identity\s+theft|confidential\s+information)", "Privacy / PII"),
            (r"(?i)(weapon|bomb|explosive|chemical\s+weapon|hardware\s+store\s+items|firearms)", "Indiscriminate Weapons"),
            (r"(?i)(counterfeit|insider\s+trading|fraud|steal\s+money|steal\s+from\s+a\s+charity|manipulate\s+stock)", "Non-Violent Crimes"),
            (r"(?i)(physically\s+assault|cause\s+physical\s+harm|incite\s+violence|hate\s+speech|racism|cyberbully|poison\s+a\s+person)", "Violent Crimes"),
            (r"(?i)(suicide|self-harm|anorexia|bulimia)", "Suicide / Self-Harm"),
            (r"(?i)(forcefully\s+terminate|kill\s+daemon|unauthorized\s+access|excessive\s+agency)", "Non-Violent Crimes"),
        ]

    def _fallback_scan(self, user_prompt: str) -> Dict[str, Any]:
        """Perform heuristic safety taxonomy classification if remote API is unavailable."""
        for pattern, category in self.fallback_taxonomy:
            if re.search(pattern, user_prompt):
                return {
                    "passed": False,
                    "verdict": "unsafe",
                    "violated_codes": ["S13"],
                    "violated_categories": [category],
                    "reason": f"Safety policy violation [{category}]"
                }
        return {
            "passed": True,
            "verdict": "safe",
            "violated_codes": [],
            "violated_categories": [],
            "reason": None
        }

    def scan_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Evaluates input intent against the Llama Guard safety policy via Groq API,
        falling back to local taxonomy evaluation if unconfigured.
        """
        if not self.client:
            return self._fallback_scan(user_prompt)

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content moderation guardrail. Evaluate the user prompt against standard safety taxonomies. Output ONLY 'safe' if benign, or 'unsafe\\nS<number>' (e.g., unsafe\\nS13 for cyberattacks) if malicious. Do not include any other text."
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=self.model_id,
            )
            
            result_text = chat_completion.choices[0].message.content.strip()
            lines = result_text.split("\n")
            decision = lines[0].strip().lower()
            
            if decision == "safe":
                return {
                    "passed": True,
                    "verdict": "safe",
                    "violated_categories": [],
                    "reason": None
                }
            else:
                violated_codes = [code.strip() for code in lines[1:] if code.strip()] if len(lines) > 1 else []
                violated_categories = [self.category_map.get(code, code) for code in violated_codes]
                
                return {
                    "passed": False,
                    "verdict": "unsafe",
                    "violated_codes": violated_codes,
                    "violated_categories": violated_categories,
                    "reason": f"Safety policy violation: {', '.join(violated_categories) if violated_categories else 'Unsafe content'}"
                }
        except Exception:
            # Fallback in case API fails or times out
            return self._fallback_scan(user_prompt)
import os
from typing import Dict, Any

try:
    from groq import Groq
except ImportError:  # pragma: no cover - dependency may be unavailable in local/offline installs.
    Groq = None


class LlamaGuardScanner:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key and Groq is not None else None
        self.model_id = "openai/gpt-oss-safeguard-20b"
        
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

    def scan_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Evaluates input intent against the Llama Guard safety policy via Groq API.
        """
        if not self.client:
            return {
                "passed": True,
                "verdict": "skipped",
                "violated_codes": [],
                "violated_categories": [],
                "reason": "LlamaGuard skipped (GROQ_API_KEY not configured)"
            }

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
            
            # The model outputs a simple string like 'safe' or 'unsafe\nS13'
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
        except Exception as e:
            # Failsafe in case the API drops
            return {
                "passed": False,
                "verdict": "error",
                "violated_codes": [],
                "violated_categories": [],
                "reason": f"API Error: {str(e)}"
            }
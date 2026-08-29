import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "llm_defense_proxy")))
from main import app

__all__ = ["app"]

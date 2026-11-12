"""
services/agent_runtime/src/llm_gateway.py
Universal LLM Gateway for Project Aethelgard Autonomous Virtual Studio.
Features:
- Persistent cumulative spend ledger (build/staging/spend_ledger.json) across CLI runs
- Hard $1.00 budget circuit breaker
- Zero-Thinking-Token configuration (thinkingBudget: 0)
- SHA-256 disk caching ($0.00 repeat queries)
"""

import os
import json
import logging
import hashlib
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("Studio.LLMGateway")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _load_dotenv(workspace_root: Path):
    env_file = workspace_root / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_load_dotenv(_WORKSPACE_ROOT)


class LLMGateway:
    MAX_BUDGET_USD = 1.00
    RATE_INPUT_PER_MTOK = 0.30
    RATE_OUTPUT_PER_MTOK = 2.50

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or _WORKSPACE_ROOT
        _load_dotenv(self.workspace_root)

        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.model = os.environ.get("STUDIO_MODEL", "gemini-flash-latest")

        self.cache_dir = self.workspace_root / "build" / "staging" / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.workspace_root / "build" / "staging" / "spend_ledger.json"

        self.last_call_timestamp = 0.0
        self.min_interval_seconds = 3.5

        ledger = self._load_ledger()
        self.total_input_tokens = ledger.get("total_input_tokens", 0)
        self.total_output_tokens = ledger.get("total_output_tokens", 0)
        self.total_spend_usd = ledger.get("total_spend_usd", 0.0)
        self.total_calls = ledger.get("total_calls", 0)
        self.cache_hits = ledger.get("cache_hits", 0)

        if self.gemini_key:
            self.provider = "gemini"
        else:
            self.provider = "mock"
            logger.warning("[LLMGateway] No API key detected. Running in mock fallback mode.")

    def _load_ledger(self) -> Dict[str, Any]:
        if self.ledger_file.exists():
            try:
                return json.loads(self.ledger_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"total_input_tokens": 0, "total_output_tokens": 0, "total_spend_usd": 0.0, "total_calls": 0, "cache_hits": 0}

    def _save_ledger(self) -> None:
        try:
            self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "model": self.model,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_spend_usd": round(self.total_spend_usd, 6),
                "budget_cap_usd": self.MAX_BUDGET_USD,
                "total_calls": self.total_calls,
                "cache_hits": self.cache_hits
            }
            self.ledger_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def is_live(self) -> bool:
        return self.provider != "mock"

    def _get_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        h = hashlib.sha256()
        h.update(self.model.encode("utf-8"))
        h.update(system_prompt.strip().encode("utf-8"))
        h.update(user_prompt.strip().encode("utf-8"))
        return h.hexdigest()

    def _read_cache(self, cache_key: str) -> Optional[str]:
        cache_file = self.cache_dir / f"{cache_key}.txt"
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _write_cache(self, cache_key: str, content: str) -> None:
        try:
            cache_file = self.cache_dir / f"{cache_key}.txt"
            cache_file.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def _track_spend(self, in_tokens: int, out_tokens: int, thought_tokens: int = 0) -> float:
        ledger = self._load_ledger()
        total_out = out_tokens + thought_tokens
        call_cost = (in_tokens / 1_000_000 * self.RATE_INPUT_PER_MTOK) + (total_out / 1_000_000 * self.RATE_OUTPUT_PER_MTOK)

        self.total_input_tokens = ledger.get("total_input_tokens", 0) + in_tokens
        self.total_output_tokens = ledger.get("total_output_tokens", 0) + total_out
        self.total_spend_usd = ledger.get("total_spend_usd", 0.0) + call_cost
        self.total_calls = ledger.get("total_calls", 0) + 1
        self.cache_hits = ledger.get("cache_hits", 0)
        self._save_ledger()

        logger.info(
            f"[Budget Watchdog] +{in_tokens} in / +{out_tokens} out (+{thought_tokens} thought) | "
            f"Call: ${call_cost:.5f} | Cumulative Ledger: ${self.total_spend_usd:.4f} / ${self.MAX_BUDGET_USD:.2f}"
        )
        return call_cost

    def _pace_requests(self):
        elapsed = time.time() - self.last_call_timestamp
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        self.last_call_timestamp = time.time()

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        cache_key = self._get_cache_key(system_prompt, user_prompt)
        cached_response = self._read_cache(cache_key)
        if cached_response is not None:
            ledger = self._load_ledger()
            self.cache_hits = ledger.get("cache_hits", 0) + 1
            self._save_ledger()
            logger.info(f"[LLMGateway] Cache HIT [{cache_key[:8]}] (Cost: $0.00000 | Total Hits: {self.cache_hits})")
            return cached_response

        ledger = self._load_ledger()
        if ledger.get("total_spend_usd", 0.0) >= self.MAX_BUDGET_USD:
            logger.error(f"[Budget Circuit Breaker] Cumulative spend (${ledger['total_spend_usd']:.4f}) reached cap (${self.MAX_BUDGET_USD:.2f})!")
            return ""

        self._pace_requests()

        is_json_request = "valid JSON" in user_prompt or "JSON object" in user_prompt or "JSON array" in user_prompt
        gen_config = {
            "temperature": temperature,
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingBudget": 0}
        }
        if is_json_request:
            gen_config["responseMimeType"] = "application/json"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": gen_config
        }

        for attempt in range(2):
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    usage = res_json.get("usageMetadata", {})
                    in_tok = usage.get("promptTokenCount", len(user_prompt) // 4)
                    out_tok = usage.get("candidatesTokenCount", 0)
                    thought_tok = usage.get("thoughtsTokenCount", 0)
                    self._track_spend(in_tok, out_tok, thought_tok)

                    candidates = res_json.get("candidates", [])
                    if candidates:
                        finish_reason = candidates[0].get("finishReason", "STOP")
                        if finish_reason == "MAX_TOKENS":
                            logger.error("[LLMGateway] Output truncated due to MAX_TOKENS! Discarding.")
                            return ""
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                            if text:
                                if is_json_request:
                                    json.loads(text)
                                self._write_cache(cache_key, text)
                                return text
                break
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 400 and "thinkingConfig" in err_body and attempt == 0:
                    payload["generationConfig"].pop("thinkingConfig", None)
                    continue
                logger.error(f"[LLMGateway] Gemini HTTP {e.code} Error: {err_body}")
                break
            except Exception as e:
                logger.error(f"[LLMGateway] Error querying Gemini: {e}")
                break

        return ""

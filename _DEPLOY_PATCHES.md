# Patches to apply on your machine (sandbox truncates >15.8 KB writes)

First restore the clipped files:
```bash
git checkout -- server/mcp_server.py engine/validator.py
```
Then apply the two changes below and verify:
```bash
python -c "import ast; ast.parse(open('server/mcp_server.py').read()); ast.parse(open('engine/validator.py').read()); print('syntax OK')"
python -c "import server.mcp_server; print('import OK')"
```

---

## 1) engine/validator.py — make Pass-2 model-agnostic

### 1a. Replace `api_available()` and `_get_api_client()` with:
```python
def _validator_provider() -> str:
    # Pass-2 runs on whatever model the deployment uses -- model-agnostic.
    # Defaults to the referee's default provider; override with
    # GREYHAWK_VALIDATOR_PROVIDER (deepseek | openai | openrouter | ollama).
    return os.environ.get("GREYHAWK_VALIDATOR_PROVIDER", "deepseek")

def api_available() -> bool:
    try:
        from referee.config import get_config
        cfg = get_config(_validator_provider())
        return cfg.provider == "ollama" or bool(cfg.api_key)
    except Exception:
        return bool(os.environ.get("ANTHROPIC_API_KEY")
                    or os.environ.get("DEEPSEEK_API_KEY")
                    or os.environ.get("OPENAI_API_KEY")
                    or os.environ.get("OPENROUTER_API_KEY"))

def _get_api_client():
    # Reuse the engine's OpenAI-compatible client (DeepSeek/OpenAI/OpenRouter/
    # Ollama / any compatible proxy) instead of a Claude-specific SDK.
    global _API_CLIENT
    if _API_CLIENT is None:
        from referee.llm import OpenAICompatibleClient
        from referee.config import get_config
        _API_CLIENT = OpenAICompatibleClient(get_config(_validator_provider()))
    return _API_CLIENT
```

### 1b. Insert these three helpers immediately BEFORE `def validate_dm_response_api(`:
```python
def pass2_system_prompt() -> str:
    return _API_VALIDATOR_PROMPT


def pass2_user_input(narrative: str, context: str = "",
                     character_name: str = "") -> str:
    return (
        f"GAME CONTEXT:\n{context}\n\n"
        f"CHARACTER: {character_name}\n\n"
        f"DM NARRATIVE TO CHECK:\n{narrative}"
    )


def parse_pass2_verdict(verdict_text: str, narrative: str = "") -> dict:
    verdict_text = verdict_text or ""
    upper = verdict_text.upper()
    verdict_lines = [ln.strip() for ln in verdict_text.strip().splitlines() if ln.strip()]
    final_line = verdict_lines[-1] if verdict_lines else ""
    is_clean = (
        "CLEAN" in final_line.upper() or
        ("VIOLATION" not in final_line.upper() and verdict_text.upper().count("FAIL") == 0)
    )
    rules_failed = []
    seen = set()
    for line in verdict_text.splitlines():
        if "FAIL" not in line.upper():
            continue
        for label in _API_RULE_LABELS:
            if label in line and label not in seen:
                rules_failed.append(label); seen.add(label)
    if not rules_failed and "VIOLATION" in upper:
        m = re.search(r'VIOLATION\s*[—\-:]\s*(.+)', verdict_text)
        if m:
            tail = m.group(1)
            for label in _API_RULE_LABELS:
                if label in tail and label not in seen:
                    rules_failed.append(label); seen.add(label)
    rules_failed = [r for r in rules_failed if r not in _DISABLED_RULES]
    is_clean = is_clean or not rules_failed
    return {"clean": is_clean, "available": True, "rules_failed": rules_failed,
            "verdict": verdict_text, "original_response": narrative}
```

### 1c. Inside `validate_dm_response_api(...)`, replace EVERYTHING from `check_input = (` through the final `return { ... }` with:
```python
    check_input = pass2_user_input(narrative, context, character_name)
    _resp = _get_api_client().chat(
        messages=[
            {"role": "system", "content": _API_VALIDATOR_PROMPT},
            {"role": "user", "content": check_input},
        ],
    )
    return parse_pass2_verdict(_resp.text or "", narrative)
```

---

## 2) server/mcp_server.py — sampling-first Pass-2 ladder

### 2a. Replace the whole `def _do_dm_response(...)` function with:
```python
def _pass1_violations(narrative, ctx, pc):
    res = _validator.validate_dm_response(narrative, context=ctx, character_name=pc)
    return list(res.get("violations", []))

def _provider_pass2_violations(narrative, ctx, pc):
    out = []
    if _validator.api_available():
        try:
            api = _validator.validate_dm_response_api(narrative, context=ctx, character_name=pc)
            out = [{"rule": r, "detail": "Pass-2 (configured model) flag."}
                   for r in api.get("rules_failed", [])]
        except Exception:
            pass
    return out

async def _sampling_pass2_violations(narrative, ctx, pc):
    try:
        session = server.request_context.session
    except Exception:
        return None
    try:
        result = await session.create_message(
            messages=[types.SamplingMessage(role="user",
                content=types.TextContent(type="text",
                    text=_validator.pass2_user_input(narrative, ctx, pc)))],
            system_prompt=_validator.pass2_system_prompt(),
            max_tokens=600, temperature=0.0)
    except Exception:
        return None
    text = ""
    content = getattr(result, "content", None)
    if content is not None:
        text = getattr(content, "text", "") or ""
    parsed = _validator.parse_pass2_verdict(text, narrative)
    return [{"rule": r, "detail": "Pass-2 (client model via sampling) flag."}
            for r in parsed.get("rules_failed", [])]

def _finish_dm_response(narrative, violations):
    if not violations:
        _ATTEMPT["count"] = 0; _DELIVERY["method"] = "dm_response"
        return {"status": "deliver", "narrative": narrative}
    _ATTEMPT["count"] += 1
    if _ATTEMPT["count"] >= 2:
        _ATTEMPT["count"] = 0; _DELIVERY["method"] = "dm_response"
        return {"status": "deliver_flagged", "narrative": narrative,
                "violations": violations,
                "note": "Force-delivered after one rewrite; the flag may be a "
                        "false positive -- if so, ship it and move on."}
    return {"status": "rejected", "violations": violations,
            "reason": "Rewrite this beat and resend through dm_response: "
                      + "; ".join(v.get("detail", "") for v in violations)}

def _do_dm_response(narrative: str = "") -> dict:
    ctx, pc = _context(), _pc_name()
    violations = _pass1_violations(narrative, ctx, pc)
    if not violations:
        violations += _provider_pass2_violations(narrative, ctx, pc)
    return _finish_dm_response(narrative, violations)

async def _do_dm_response_async(narrative: str = "") -> dict:
    ctx, pc = _context(), _pc_name()
    violations = _pass1_violations(narrative, ctx, pc)
    if not violations:
        sampled = await _sampling_pass2_violations(narrative, ctx, pc)
        if sampled is None:
            violations += _provider_pass2_violations(narrative, ctx, pc)
        else:
            violations += sampled
    return _finish_dm_response(narrative, violations)
```

### 2b. In `call_tool(...)`, replace the dispatch body with:
```python
    if name == "dm_response":
        result = await _do_dm_response_async(**(arguments or {}))
    else:
        handler = _DISCIPLINE_HANDLERS.get(name)
        if handler is not None:
            result = handler(**(arguments or {}))
        else:
            result = _TOOLS.dispatch(name, arguments or {})
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]
```

(The `_DISCIPLINE_HANDLERS` map can keep `"dm_response": _do_dm_response` as a fallback; `call_tool` intercepts it first.)

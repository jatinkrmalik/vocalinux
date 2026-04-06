# Issue #391: fix(ibus): probe engine readiness at startup and harden NO_ENGINE retries

## Description

## Summary
- Add a startup readiness handshake to the IBus injection path: after `switch_engine(vocalinux)` succeeds, `IBusTextInjector` now probes the engine socket with `\x00PING` and waits until it returns `OK` (or fails fast with `IBusSetupError`).
- Extend the engine socket protocol to support `PING` without attempting text injection, returning `OK` when `_active_instance` is ready and `NO_ENGINE` otherwise.
- Replace flat retry behavior during text injection with bounded exponential backoff for `NO_ENGINE` responses and update tests to validate the new startup + retry flow.

## Why this fixes the failure
The observed failure (`Text injection failed: NO_ENGINE`) happens when startup reports success before the engine has finished `do_enable()` and set `_active_instance`.

### Previous flow
1. Start engine process
2. Wait for socket file to exist
3. `switch_engine(vocalinux)`
4. Return success
5. First transcription attempts injection
6. Engine still not enabled -> `NO_ENGINE`

### New flow
1. Start engine process
2. `switch_engine(vocalinux)`
3. Readiness loop sends `PING` to engine socket
4. Waits for `OK` (active instance ready), with bounded backoff
5. If never ready, raises `IBusSetupError` during startup so normal backend fallback can occur
6. First transcription happens only after engine readiness is confirmed

## Validation
- `pytest tests/test_ibus_engine.py tests/test_ibus_engine_core.py`
- Result: **121 passed**

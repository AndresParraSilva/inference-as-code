# Phase 7 — Service Persistence

**Status: deferred.** This phase is conditional in the plan — a systemd unit only makes sense once there's an actual long-running process to keep alive. Right now `chess-agent-lab/agents/orchestrator.py` is a one-shot CLI: it runs once per FEN and exits. There's nothing to persist yet.

**Decision (2026-07-07):** skip for now rather than invent a service just to fill the phase number. Revisit once a real long-running job exists — e.g. if the agent grows into an HTTP API server, a scheduler, or a queue consumer. At that point this doc gets replaced with the actual systemd unit (`configs/chess-agent.service`) and its install script, following the same pattern as every other phase (script first, run second, commit third).

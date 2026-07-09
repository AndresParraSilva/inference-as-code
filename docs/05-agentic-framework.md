# Phase 6 — Agentic Framework Layer

## Scaffold

```
chess-agent-lab/
├── agents/
│   ├── orchestrator.py       # act → observe → reason loop
│   └── worker_stockfish.py   # objective evaluation via the Stockfish UCI engine
├── data/                     # gitignored — Lichess DB, PGNs stay local
├── tests/
│   └── test_worker_stockfish.py
├── pyproject.toml            # dependency declarations
├── uv.lock                   # exact resolved versions, committed alongside
└── README.md
```

Kept inside this repo (see `constitution.md` §2) rather than split into a second repo, so the whole thing reads as one self-contained example: infra plus a real application running on it.

## First task: FEN explain + Stockfish verify

**User's call** (non-delegable per `constitution.md` §10): given a FEN position, the local LLM explains the position and names its best move; Stockfish independently computes the objectively best move and evaluation; the loop compares them.

**Why hand-rolled first, no framework:** the plan calls for seeing the raw act-observe-reason mechanics — a plain loop hitting Ollama's API directly and comparing against Stockfish — before introducing LangGraph. `pyproject.toml` already declares `langgraph`/`langchain`/`langchain-community` for when that's the next step, but `orchestrator.py` only imports `ollama` and `chess` for now. (`crewai` was originally pinned here too — see the third gotcha below for why it was dropped.)

## Dependency management: uv

Switched from a plain `requirements.txt` + `venv` to [`uv`](https://astral.sh/uv) — dependencies are declared in `pyproject.toml`, and `uv lock` resolves the *entire* dependency tree (161 packages, not just the 7 direct ones) into `uv.lock`, which is committed alongside it. That's a stronger reproducibility guarantee than `requirements.txt` ever gave: two machines running `uv sync` against the same `uv.lock` get byte-identical resolved versions, transitive dependencies included.

## Gotcha: matching the system Python was the wrong call

The first version of `pyproject.toml` pinned `requires-python` to match whatever Python the box's OS shipped — first assumed `3.12` (from an incorrect assumption the box ran Ubuntu 24.04; it actually runs **Ubuntu 26.04 LTS**, correction applied throughout this repo), then corrected to the box's real system Python, `3.14.4`.

Neither worked. On Python 3.14, `import crewai` crashes outright:
```
pydantic.v1.errors.ConfigError: unable to infer type for attribute "chroma_server_nofile"
```
**Root cause:** `crewai` pulls in `chromadb`, which still relies on Pydantic's legacy `v1` compatibility shim internally — and that shim is explicitly broken on Python 3.14 (`chromadb` itself prints `UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater`). This is an upstream ecosystem gap, not something fixable from this repo.

**Fix:** stop trying to match the OS's system Python at all. `requires-python` is now `>=3.13,<3.14`, and `uv` manages its *own* Python 3.13 interpreter for this project — completely decoupled from whatever the box's `python3` happens to be. `uv sync` downloads that interpreter itself if it's not already present (as it did here, and will on the box too).

**Lesson:** tying a project's Python version to "whatever the OS ships" is fragile precisely because OS upgrades change that version out from under you. Letting `uv` own the interpreter version is the more idiomatic use of the tool — it's the entire reason project-scoped, uv-managed Pythons exist. Verify actual system facts (`ssh iac 'python3 --version'`) rather than assuming from the OS version number; two assumptions here (24.04 → 3.12, then "match the system") were both wrong before landing on the right one.

## Gotcha: critical, unpatched RCE in a transitive dependency

GitHub's Dependabot flagged a **critical** vulnerability on the pushed `uv.lock`: `chromadb` 1.1.1, pulled in transitively via `crewai` 1.15.1.

**The vulnerability:** an unauthenticated, pre-auth code injection in ChromaDB's `/api/v2/tenants/{tenant}/databases/{db}/collections` endpoint — sending a malicious model repository with `trust_remote_code=true` lets an attacker run arbitrary code on the server. Affects `chromadb` `>=1.0.0`, up to and including the current latest release, `1.5.9` — **there is no patched version to upgrade to.**

**Why this repo isn't actually exposed right now:** `chromadb`'s vulnerable surface is its *server* API — reachable only if something starts a ChromaDB server and a client sends it a crafted request. `orchestrator.py` doesn't import `crewai` at all yet (§ First task, above); `crewai`/`chromadb` are reserved dependencies for a later phase, not in use. Even if they were, `crewai`'s default usage runs `chromadb` embedded (in-process), not as an exposed server. And even in the worst case, the firewall from Phase 3 (`scripts/02-firewall.sh`) only allows inbound `22/tcp` and `11434/tcp` — nothing would make a `chromadb` server reachable from the LAN without a deliberate, separate firewall change.

**Fix at the time, rather than just accepting the risk:** `uv` supports forcing a transitive dependency to a different version than what the dependent package requests (`[tool.uv] override-dependencies`). Forced `chromadb` down to `0.6.3` — the last release before `1.0.0`, entirely outside the affected range — and verified `crewai` still imports cleanly against it:
```toml
[tool.uv]
override-dependencies = ["chromadb<1.0.0"]
```

**Superseded:** this override is what caused the third gotcha below (a build failure for `chromadb<1.0.0`'s own C-extension dependency, `chroma-hnswlib`, on the box). `crewai` — and with it this whole override — was dropped rather than chased further. Left here as a record of what was tried, not current state.

## Gotcha: crewai dropped after a second real breakage

After the Python-version fix and the CVE override above, `uv run python -m unittest discover tests` failed on the box (not locally) trying to *build* `chroma-hnswlib==0.7.6` — the C-extension dependency the downgraded `chromadb<1.0.0` pulls in:
```
RuntimeError: Unsupported compiler -- at least C++11 support is needed!
```
despite the build log showing the compiler successfully compiling both test snippets it tried (`-std=c++14` and `-std=c++11`) immediately beforehand.

**Root cause:** no prebuilt wheel exists for `chroma-hnswlib==0.7.6` on Python 3.13 at all (confirmed against PyPI directly) — it must compile from source on every machine. Its `setup.py` is old, unmaintained `pybind11`-era code with a `cpp_flag()` compiler-detection routine that doesn't correctly interpret results from newer compilers; Ubuntu 26.04 ships a much newer `g++`/`clang` than that 2023-era detection code was written against. The compiler worked fine — the package's own bookkeeping about it didn't. This didn't surface locally, only on the box, because the box's compiler version differs.

**Why not chase this further:** this is the *second* real breakage caused by the exact same unused dependency chain (`crewai` → `chromadb` → `chroma-hnswlib`) — first the Python 3.14 incompatibility, now this. `crewai` still isn't imported by any code. Patching a legacy build script, or pinning a specific system compiler version just to satisfy a dependency added purely for future use, isn't a good trade.

**Fix:** drop `crewai` from `pyproject.toml` entirely (and with it, the now-moot `chromadb` override above). Re-add it later if a phase actually needs it — by then `chromadb` will likely have a genuinely patched release, resolving both this build issue and the CVE at once, rather than requiring another workaround.

**Lesson:** pinning a framework "for later" isn't free even if unused — its transitive dependencies still have to resolve, build, and import correctly on the actual target machine. Two independent failures from one never-imported package is a signal to cut it, not patch around it a second time.

Direct dependencies, exact versions captured from PyPI when this phase landed (`pip index versions <pkg>`), minus `crewai` per the gotcha above:
```
langgraph==1.2.7
langchain==1.3.11
langchain-community==0.4.2
ollama==0.6.2
duckdb==1.5.4
chess==1.11.2
```

## Provisioning: git clone instead of scp

`scripts/05-chess-agent-setup.sh` departs from the scp-a-single-script pattern used in earlier phases (`docs/scripts.md`) because this phase is multiple files (two Python modules, a test, `pyproject.toml`, `uv.lock`), not one script. Instead it:

1. Installs the `stockfish` engine binary (`apt`), and `uv` itself via its official installer script (if not already present).
2. `git clone`s (or `git pull`s, if already present) this public repo directly onto the box, at `~/inference-as-code` — the repo's own public GitHub URL is hardcoded since it's not a secret, it's the reproducibility target.
3. Runs `uv sync` inside `chess-agent-lab/`, which creates the venv and installs the exact locked versions from `uv.lock` — no separate `python3-venv`/`python3-pip` apt packages needed, since `uv` manages venv creation itself.

This means the box now carries a full read-only checkout of the repo it's part of — a reasonable analogue to `git pull`-based deploys, and it solves keeping multiple application files in sync without scp-ing them one by one.

## Why Stockfish needs a system binary

`python-chess`'s `chess.engine` module doesn't include an engine itself — it speaks the UCI protocol to an external binary. `apt install stockfish` provides that binary on `$PATH`; `worker_stockfish.py` defaults to just `"stockfish"` (overridable via `STOCKFISH_PATH`) rather than hardcoding an install path.

## Run it

```bash
ssh iac
cd inference-as-code/chess-agent-lab
uv run agents/orchestrator.py
```

`OLLAMA_HOST` defaults to `http://localhost:11434` — this runs entirely on the box, hitting its own local Ollama instance.

## Tests

```bash
uv run python -m unittest discover tests
```

`test_worker_stockfish.py` skips (rather than fails) if no `stockfish` binary is on `PATH` — an external system dependency, not a Python package, so its absence is an environment precondition rather than a code defect.

## Checkpoint

✅ Ran on the box: `uv run agents/orchestrator.py` against the starting position. `llama3.2:3b` explained the position and named `e4` as its suggested move; Stockfish independently confirmed `e4` as its own best move (+39 centipawns). Verdict: match. The full hand-rolled act-observe-reason loop works end to end.

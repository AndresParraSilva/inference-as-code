# Phase 5 — Inference Engine: Ollama

## Install and LAN exposure

`scripts/04-ollama.sh`:
1. Installs Ollama via the official install script.
2. Drops a systemd override at `/etc/systemd/system/ollama.service.d/override.conf` (mirrored in `configs/ollama-override.conf`) setting `OLLAMA_HOST=0.0.0.0:11434` — by default Ollama binds only to `localhost`, which would make it unreachable from any other machine on the LAN.
3. Enables and restarts the `ollama` service.
4. Pulls the starter models.

**Why 0.0.0.0 is safe here:** the firewall from Phase 3 (`scripts/02-firewall.sh`) already scopes inbound access to `11434/tcp` specifically, on a deny-by-default posture — binding Ollama to all interfaces only matters within that already-restricted LAN surface, not the open internet.

## Model selection: what fits in 8GB RAM

| Model | Quantization | Why this one |
|---|---|---|
| `qwen2.5:3b` | Q4 (default) | Smallest starter model — fast responses, low RAM footprint, good baseline for interactive use |
| `llama3.2:3b` | Q4 (default) | Second 3B-class model for comparison — different training/tuning, same size class |
| `qwen2.5:7b-instruct` | Q4_K_M | Largest model that still comfortably fits an 8GB, CPU-only, headless box |

**Why quantization matters here:** full-precision (FP16) weights for a 7B model need roughly 14GB of RAM just to load — impossible on this hardware. Q4 quantization (4-bit weights) shrinks that to roughly a quarter, at a modest, usually acceptable cost in output quality — the tradeoff that makes a 7B model usable at all on a CPU-only 8GB machine. `Q4_K_M` specifically is a good default: it mixes precision across tensor types (keeping more bits where it matters most for quality) rather than quantizing everything uniformly.

No model beyond 7B is attempted — with the OS, Ollama runtime, and any agent tooling from Phase 6 also competing for the same 8GB, headroom above a 7B Q4 model runs out fast.

## Checkpoints (non-delegable — hardware/network judgment calls)

1. **Speed sanity check, on the box:** run a model directly and judge whether tokens/sec feels usable for your intended use case:
   ```bash
   ollama run qwen2.5:3b "Explain the Sicilian Defense in two sentences."
   ```
2. **Hit the API from the main machine** — the "private EC2 endpoint" proof:
   ```bash
   curl http://iac.local:11434/api/generate -d '{
     "model": "qwen2.5:3b",
     "prompt": "Explain the Sicilian Defense in two sentences.",
     "stream": false
   }'
   ```
   (Or `192.168.x.x` if mDNS resolution isn't working yet.)

Real tokens/sec, time-to-first-token, and peak RAM numbers for each model are measured properly in Phase 8 (`bench/benchmark.py`) — these checkpoints are just a go/no-go gut check before investing further.

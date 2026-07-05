# inference-as-code

A decommissioned Dell Latitude 5410 turned into an EC2-style headless AI lab — CPU-only local LLM inference with agentic frameworks, built and documented like cloud infrastructure.

**Goal:** turn the laptop into a headless "AI lab server" that behaves like an AWS EC2 instance — same mental model, same access pattern, same discipline — and document the entire process as a reproducible, public build log. Every script, config, and doc in this repo is committed as the work happens, not written up after the fact.

The conventions that govern every change in this repo (stack, script standards, sanitization rules, git discipline) live in [constitution.md](constitution.md).

## AWS → Local Mental Model

| AWS EC2 concept | Local equivalent | Phase |
|---|---|---|
| Choosing an AMI | Ubuntu Server 24.04 LTS ISO | 1 |
| Launching the instance | Installing the OS on the Latitude | 1 |
| Security Group (firewall rules) | UFW rules | 3 |
| Key Pair (.pem) for SSH | Ed25519 SSH keypair | 4 |
| IAM user (no root login) | Dedicated non-root sudo user | 4 |
| Elastic IP / private DNS | Static local IP + mDNS hostname (`latitude-ai.local`) | 3 |
| `aws ssm start-session` / SSH | `ssh youruser@latitude-ai.local` | 4 |
| User-data script (bootstrap on launch) | Idempotent `bootstrap.sh` — versioned in the repo | 2–7 |
| Infrastructure as Code (CloudFormation/Terraform) | All configs/scripts committed to Git — the repo IS the IaC | all |
| systemd service | `ollama.service`, custom agent services | 7 |
| CloudWatch logs / metrics | `journalctl`, `htop`/`btop`, benchmark logs | 8 |
| S3 bucket for shared files | `/srv/shared` over SSH (SSHFS/scp/rsync) | 3 |
| Tagging resources | Naming conventions (`chess-agent-*`) | throughout |
| AWS reference architecture blog post | This README + a LinkedIn writeup | 9–10 |

## Status

🚧 Early build-out — following the phased plan below. Docs, scripts, configs, and benchmarks land here as each phase completes.

## Repo structure (target)

```
.
├── README.md
├── constitution.md # technical authority — conventions every change must follow
├── LICENSE
├── docs/           # per-phase notes (install, network, access, inference, architecture)
├── scripts/        # numbered, idempotent, runnable in order
├── configs/        # systemd units, service overrides
└── bench/          # benchmark suite + results
```

## Reproduce this

See [`docs/scripts.md`](docs/scripts.md) for the general workflow (how scripts run on the box, in what order).

1. Install the OS — see [`docs/01-install.md`](docs/01-install.md).
2. Base configuration ("AMI hardening") — run [`scripts/01-base-setup.sh`](scripts/01-base-setup.sh).
3. Network & firewall ("Security Group") — run [`scripts/02-firewall.sh`](scripts/02-firewall.sh); see [`docs/02-network.md`](docs/02-network.md).

More steps land here as each phase completes (access hardening, inference engine, ...).

## Related

- Chess analysis agent (LangGraph + local LLMs, built on top of this lab): link TBD

## License

MIT — see [LICENSE](LICENSE).

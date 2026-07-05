# Phase 3 — Network & Security ("Security Group")

## DHCP reservation

The Latitude's MAC address is reserved on the router (mapped to a fixed LAN IP) — the local equivalent of an Elastic IP. This is a router-side, non-automatable step done outside this repo.

Confirmed via the router's admin panel — the box's MAC now has an explicit static-lease entry, so the IP survives reboots and lease renewals rather than just persisting by DHCP-lease coincidence.

## Firewall — UFW as the Security Group

`scripts/02-firewall.sh` applies a deny-by-default posture:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 11434/tcp comment 'Ollama API'
sudo ufw --force enable
```

**Why deny-by-default:** the safe default for any network-facing box is to reject everything unless explicitly allowed, then open only the ports a real use case needs — the same posture as an AWS Security Group with no inbound rules until you add them. Two inbound allowances exist right now:

- **OpenSSH** — the only remote access path onto the box.
- **11434/tcp (Ollama API)** — opened ahead of Phase 5 so the LAN can reach Ollama once it's installed; scoped to a single port rather than a broad range.

Outgoing traffic is allowed by default since the box needs to reach `apt` mirrors, `ollama.com`, and model registries — restricting egress isn't a goal here.

## Shared files

`/srv/shared` over SSH (SSHFS, `scp`, or `rsync`) is the plan for ad-hoc file transfer — reuses the same Ed25519 key-based auth from Phase 4 rather than opening a dedicated port (e.g. Samba). Decision deferred until there's an actual file-sharing need.

## Sanitization reminder

Per `constitution.md` §6: no real LAN IPs, MAC addresses, or hostnames beyond generic examples in any committed file — this doc and all others use `192.168.x.x` placeholders.

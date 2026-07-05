# Phase 1 — Physical Setup & OS Install

Non-automatable phase: physical access, BIOS, and the installer TUI. Notes below written from memory right after install, for anyone reproducing the setup.

## Installer image

**Ubuntu Server** (standard), not "Ubuntu Server (minimized)".

**Why:** the minimized variant targets cloud instances nobody logs into interactively — it strips tooling, docs, and conveniences to shrink the image. This box gets SSHed into constantly (running scripts, `journalctl`, `htop`), so the standard flavor is the right fit. The RAM savings the plan cares about (~1.5–2GB) come from having no GUI, which is true of both variants — minimized buys almost nothing here while making interactive work more annoying.

## Third-party drivers

Checked "Search for third-party drivers".

**Why:** the Latitude 5410 is all-Intel hardware (Comet Lake CPU/graphics, Intel Wi-Fi) — fully supported by the mainline kernel, so there was nothing third-party to find in practice. That option mainly matters for NVIDIA GPUs or some Broadcom Wi-Fi chips. Checking it costs nothing and covers the rare firmware edge case.

## BIOS/UEFI (F2 on Dell)

Two changes were required on this machine before the installer/USB would boot and see the disk correctly:

- **SATA Operation: AHCI** (was `RAID On`) — the installer couldn't see the disk correctly under RAID mode.
- **Secure Boot: disabled** (unchecked "Secure Boot Enable").

Reference followed: [Dell Latitude BIOS setup for Ubuntu install (YouTube)](https://www.youtube.com/watch?v=OLSlvCyjEZA&t=60)

- SSD set as primary boot device after install.

## Disk layout

Kept "Set up this disk as an LVM group" checked.

**Why:** LVM adds a thin abstraction layer between the disk and the filesystem, but it's the closest local analog to an EBS snapshot — a checkpoint you can take before a risky change (a big model pull, an agent experiment that could fill the disk) and roll back from if it goes wrong. Fits the AWS mental model this repo is built around.

The installer's guided LVM layout did **not** assign the full 238GB disk to the root logical volume — `df -h` shows `/` at 7.4% of 97.87GB, leaving roughly 140GB unallocated in the volume group rather than in root.

**Why not use the whole disk:** this is intentional installer behavior, not a mistake. An LVM snapshot needs free extents in the volume group to store its copy-on-write deltas — if root consumed 100% of the disk, there would be zero room to ever take a snapshot. The unallocated space is exactly what makes the snapshot capability above actually usable.

**Decision:** left as-is for now. ~90GB of headroom comfortably fits the OS plus several 3B/7B quantized models, and it's easy to grow later (`lvextend` + `resize2fs`) once real usage patterns are visible after pulling models — harder to shrink after the fact. If more root space is needed later, extend partially rather than to 100%FREE so snapshotting still has room to work, e.g.:
```bash
sudo lvextend -l +50%FREE /dev/mapper/<vg>-root
sudo resize2fs /dev/mapper/<vg>-root
```

## Installer choices

- Hostname: `iac`
- Username: iac-operator (not `admin`/`root`)
- **OpenSSH server enabled** at install time — the "allow SSH in security group" step for this box
- Snaps/extras skipped

## Checkpoint

✅ Server up. Local login confirmed once, IP noted (`ip a`).

✅ First remote SSH login confirmed from the main machine (`ssh iac-operator@192.168.x.x`), accepting the new host's ED25519 fingerprint on first connect, then authenticating with the install-time password. No monitor/keyboard needed after this point — all further work happens over SSH from Claude Code.

Next: Phase 4 — generate the dedicated `iac-lab` Ed25519 keypair and switch to key-only auth.

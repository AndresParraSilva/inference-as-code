#!/usr/bin/env bash
# scripts/01-base-setup.sh — idempotent base configuration ("AMI hardening")
set -euo pipefail

sudo apt update
sudo apt full-upgrade -y

sudo apt install -y \
  curl \
  wget \
  git \
  htop \
  btop \
  tmux \
  vim \
  ufw \
  fail2ban \
  unattended-upgrades \
  avahi-daemon

sudo systemctl enable --now avahi-daemon

sudo dpkg-reconfigure --priority=low unattended-upgrades

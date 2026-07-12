---
name: network-proxy
description: 'Automatically detect network environments (especially Mainland China), configure and verify local proxy connectivity (default port 1082), handle fallback interactions, and manage intelligent local/reverse port forwarding for SSH sessions including remote terminal proxy setup.'
---

# Network Proxy Manager

## Overview

Automate network environment detection, ensure robust proxy validation before external downloads or environment provisioning, and seamlessly extend local proxy capabilities to remote servers via SSH tunneling.

---

## Proxy Configurations

| Variable | Protocol | Default Value | Purpose |
| --- | --- | --- | --- |
| `http_proxy` | HTTP | `http://127.0.0.1:1082` | HTTP traffic routing |
| `https_proxy` | HTTPS | `http://127.0.0.1:1082` | HTTPS traffic routing |
| `all_proxy` | SOCKS5 | `socks5://127.0.0.1:1082` | Git/Ssh and global routing |

---

## Workflow & Implementations

### 1. Network Environment Detection

Before initiating any download or connection, analyze whether the current environment is behind the Great Firewall (GFW).

```bash
# Test connection to an domestic (CN) and global endpoint simultaneously
curl -I -s --connect-timeout 3 https://www.baidu.com > /dev/null && echo "Domestic: OK"
curl -I -s --connect-timeout 3 https://www.google.com > /dev/null && echo "Global: OK"

# If Domestic is OK but Global times out, flag environment as "Mainland China (Strict GFW)"

```

### 2. Pre-Flight Proxy Verification (Default Port: 1082)

Before running environment configuration tools (`apt`, `brew`, `pip`, `npm`, `wget`), execute a port and routing handshake.

```bash
# Step A: Check if local port 1082 is listening
if ! nc -z 127.0.0.1 1082; then
    echo "[ERROR] Proxy software is not running on port 1082."
    # FALLBACK: Trigger interaction to ask user for alternative port or to start proxy
fi

# Step B: Verify routing success via proxy
export http_proxy=http://127.0.0.1:1082
export https_proxy=http://127.0.0.1:1082
export all_proxy=socks5://127.0.0.1:1082

if curl -I -s --connect-timeout 5 https://www.google.com | grep -q "200\|302\|301"; then
    echo "[SUCCESS] Proxy tunnel verified. Proceeding with task."
else
    echo "[FAIL] Proxy port 1082 is open, but traffic cannot bypass GFW."
    # FALLBACK: Prompt user to check upstream nodes
fi

```

### 3. Intelligent SSH Remote Forwarding & Setup

When a task requires connecting to a remote server (`ssh`), evaluate if the remote server needs internet access (e.g., downloading packages) but lacks a functional network.

#### Decision Matrix

* **Scenario A (No Forwarding):** Remote server has its own clean international network $\rightarrow$ Standard SSH.
* **Scenario B (Reverse Port Forwarding):** Remote server is also in a restricted network and needs to borrow your local proxy $\rightarrow$ **Use SSH Reverse Tunnel**.

```bash
# Execute SSH with Reverse Port Forwarding (Maps remote 1082 to local 1082)
ssh -R 1082:127.0.0.1:1082 user@remote_server_ip

```

#### Post-Login Remote Terminal Setup

Immediately after logging into the remote server, execute the following to bind the terminal to the forwarded proxy:

```bash
# Run this on the remote terminal automatically or output as instructions
export http_proxy=http://127.0.0.1:1082
export https_proxy=http://127.0.0.1:1082
export all_proxy=socks5://127.0.0.1:1082

# Verify on remote
curl -I -s --connect-timeout 3 https://www.google.com

```

---

## Interactive Fallback Protocols

> **Protocol 1: Port Discovery**
> If `nc -z 127.0.0.1 1082` fails, the Agent must pause and output:
> *"I noticed port 1082 is closed. Are you using a different port for your proxy (e.g., 7890, 10809)? Please provide the correct port or turn on your proxy client."*

> **Protocol 2: Toggle State**
> Provide explicit commands to quickly turn off proxies when switching back to domestic-only high-speed tasks:
> `unset http_proxy https_proxy all_proxy`

---

## Proxy Safety Protocol

* **NEVER** permanently write proxy env vars into global profiles (`/etc/profile`, `~/.bashrc`) unless explicitly instructed by the user. Keep it scoped to the current shell session.
* **NEVER** share proxy credentials or upstream server IPs in logs or telemetry.
* Always use `--connect-timeout` during detection to prevent the Agent from hanging indefinitely on dead connections.

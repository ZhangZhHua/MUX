---
name: gpu10-deploy
description: Workflow instructions for committing local code, pushing to GitHub, tunneling a proxy to pull on remote server gpu10, building Docker images without cache, and reloading Nginx.
---

# GPU10 Server Pull & Rebuild Deployment Workflow

Use this skill whenever you need to deploy local code modifications to the production Docker stack on the `gpu10` server.

## Step 1: Clean Local AppleDouble Files
Clean macOS garbage metadata files from the exFAT filesystem to prevent BuildKit xattr context loading errors:
```bash
find . -name "._*" -delete
```

## Step 2: Stage, Commit, and Push Locally
Stage the code changes (ensure `DEPLOY.md` and `.env` files are ignored), commit, and push:
```bash
git add <modified-files>
git commit -m "feat/fix(scope): conventional message description"
git push origin gpu10
```

## Step 3: Remote Git Pull on Server via Local Proxy SSH Reverse Tunnel
Since `gpu10` has network constraints accessing GitHub, forward the local proxy (`127.0.0.1:1082`) to the remote port `10809` to download the commits:
```bash
ssh -R 10809:127.0.0.1:1082 gpu10 "cd /home/zhonghua/mux && git -c http.proxy=socks5://127.0.0.1:10809 pull"
```
*(Note: Do not use port 1082 on the server as it is already occupied).*

## Step 4: Rebuild Containers on Server Without Cache
Trigger a clean Docker build on the server to prevent caching issues:

- **To rebuild only the backend**:
  ```bash
  ssh gpu10 "cd /home/zhonghua/mux && find . -name '._*' -delete && docker compose -f docker-compose.prod.yml build --no-cache mux-backend && docker compose -f docker-compose.prod.yml up -d"
  ```
- **To rebuild only the frontend**:
  ```bash
  ssh gpu10 "cd /home/zhonghua/mux && find . -name '._*' -delete && docker compose -f docker-compose.prod.yml build --no-cache mux-frontend && docker compose -f docker-compose.prod.yml up -d"
  ```
- **To rebuild all containers**:
  ```bash
  ssh gpu10 "cd /home/zhonghua/mux && find . -name '._*' -delete && docker compose -f docker-compose.prod.yml build --no-cache && docker compose -f docker-compose.prod.yml up -d"
  ```

## Step 5: Flush Nginx DNS Lookup Cache
Restart the gateway container to ensure Nginx picks up the fresh IP addresses of the recreated backend/frontend containers (prevents `502 Bad Gateway`):
```bash
ssh gpu10 "docker restart mux_gateway"
```

## Step 6: Verify Deployment Status
List the active containers on `gpu10` to verify everything is in `Up` status:
```bash
ssh gpu10 "docker ps"
```

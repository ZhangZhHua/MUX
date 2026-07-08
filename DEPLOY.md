# 🚀 Server Agent Deployment & Security Playbook

This document is designed for the **Server-Side Agent** to read and execute step-by-step in order to securely deploy the **MUX (Lab Data OS)** application in the `~/mux` directory.

---

## Phase 1: Environment Variables & Security Credentials

The server-side agent must set up secure production variables.

### Step 1.1: Copy Production Env Template
Copy `.env.prod.example` to `.env.prod`:
```bash
cp ~/mux/.env.prod.example ~/mux/.env.prod
```

### Step 1.2: Generate Secure Random Secrets
Generate a strong 32-byte hexadecimal key for JWT token encryption and update the `.env.prod` file.
The agent should execute:
```bash
# Generate key
JWT_SECRET=$(openssl rand -hex 32)
echo "Generated Secret Key: $JWT_SECRET"

# Replace SECRET_KEY in .env.prod
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$JWT_SECRET|g" ~/mux/.env.prod
```

### Step 1.3: Update Database Credentials
Generate a secure password for PostgreSQL and update `.env.prod`:
```bash
DB_PASS=$(openssl rand -hex 16)
sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASS|g" ~/mux/.env.prod
```

---

## Phase 2: Launch Docker Compose Production Services

### Step 2.1: Stop Existing Development Database (If any)
If there is a container running on port 5432 (like the development database), stop it to release host resource bindings:
```bash
docker stop lab_postgres || true
```

### Step 2.2: Build and Spin Up MUX Services
Launch the services in detached mode:
```bash
cd ~/mux
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Phase 3: Database Schema Migration & Initialization

Wait for 5 seconds to ensure the PostgreSQL container is fully booted up, then run the DB initialization script inside the backend container:

```bash
# Wait for DB container to start up
sleep 5

# Execute database migrations/table creation
docker exec -t mux_backend python reset_db.py
```

---

## Phase 4: Production Security & Exposure Audit

The agent must verify that the ports are locked down.

### Step 4.1: Audit Open Ports on the Host
Verify that **ONLY port 80** is bound to the public host interface, and that the database (`5432`) and backend api (`8000`) are NOT exposed externally.
Run:
```bash
docker ps
```
**Expected Ports Alignment**:
*   `mux_gateway` should show: `0.0.0.0:80->80/tcp` (public)
*   `mux_backend` should show: `8000/tcp` (internal only, no public port mapping)
*   `mux_postgres` should show: `5432/tcp` (internal only, no public port mapping)

### Step 4.2: Verify Host Network Firewall (UFW)
Check the system firewall to make sure public ports are configured correctly:
```bash
sudo ufw status verbose
```


---

## Phase 5: Automatic HTTPS/SSL Certification (Nginx & Certbot)

If a domain name is assigned and pointed to the server, configure SSL.

### Step 5.1: Replace Hostname in Nginx Config
Ensure the Nginx configuration `/etc/nginx/conf.d/default.conf` inside the proxy has the correct domain name:
Edit `nginx/default.conf` and set the `server_name` directive to the real domain name (e.g., `mux.yourdomain.com`). Then reload Nginx:
```bash
docker exec -t mux_gateway nginx -s reload
```

### Step 5.2: Install Certbot on Host and Terminate SSL
Running Certbot on the host is highly recommended to automate SSL renewals:
```bash
# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain SSL Certificate (replace with your domain)
# Note: Ensure you configure DNS A-record first
sudo certbot --nginx -d mux.yourdomain.com --non-interactive --agree-tos -m lab-admin@yourdomain.com
```

# VPS Deployment

This path is for a plain Ubuntu 24.04 VPS with Docker and automatic HTTPS through Caddy.

## What this repo now includes

- [docker-compose.vps.yml](C:/Users/user/Documents/modelops-ai/docker-compose.vps.yml): app + Caddy reverse proxy
- [deploy/Caddyfile](C:/Users/user/Documents/modelops-ai/deploy/Caddyfile): automatic TLS and reverse proxy
- [.env.vps.example](C:/Users/user/Documents/modelops-ai/.env.vps.example): domain-level variables for HTTPS

## Before you start

You need:

1. An Ubuntu 24.04 VPS.
2. A domain or subdomain pointed at the VPS public IP with an `A` record.
3. Ports `80` and `443` open in the VPS firewall or cloud firewall.

## Server setup

SSH into the server, then install Docker Engine and the Compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

If you use UFW, allow web traffic before launch:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Clone the repo and enter it:

```bash
git clone https://github.com/mega-zod/modelops.git
cd modelops
```

Create the production env files:

```bash
cp .env.example .env
cp .env.vps.example .env.vps
```

Edit `.env` and set:

- `MODEL_OPS_API_KEY`
- `EXECUTION_APPROVAL_TOKEN`

Edit `.env.vps` and set:

- `DOMAIN`
- `ACME_EMAIL`

## Launch

Start the stack:

```bash
docker compose -f docker-compose.vps.yml up --build -d
```

Check status:

```bash
docker compose -f docker-compose.vps.yml ps
docker compose -f docker-compose.vps.yml logs -f
```

## Verify

Health should be public:

```bash
curl https://YOUR-DOMAIN/health
```

The demo walkthrough should require your API key:

```bash
curl -H "X-API-Key: YOUR_MODEL_OPS_API_KEY" https://YOUR-DOMAIN/api/v1/demo/walkthrough
```

## Updating later

From the repo directory:

```bash
git pull
docker compose -f docker-compose.vps.yml up --build -d
```

## Notes

- SQLite data persists in the Docker volume `modelops-data`.
- Generated deployment scripts persist in the Docker volume `modelops-generated`.
- Caddy stores certificates and TLS state in `caddy-data` and `caddy-config`.
- The VPS stack does not expose port `8000` publicly. Caddy is the only public entry point.

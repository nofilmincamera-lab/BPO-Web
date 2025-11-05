# Cloudflare Tunnel Access Guide

## Your Public Access URL

**Tunnel URL**: https://everybody-pastor-appearing-tell.trycloudflare.com
**Auth Token**: `b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a`

---

## What is Cloudflare Tunnel?

Cloudflare Tunnel (formerly Argo Tunnel) provides secure public access to your Vast.AI services without:
- ❌ Opening firewall ports
- ❌ Keeping SSH connections open
- ❌ Configuring port forwarding
- ✅ Just works with HTTPS!

---

## Quick Access Links

### Option 1: Direct Access with Token

Add the token as URL parameter:

**Prefect UI**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

**API**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:8000/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

**API Docs**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:8000/docs?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

### Option 2: Browser Extension (Recommended)

1. **Install ModHeader** (Chrome/Firefox extension)
2. **Add Header**:
   - Name: `CF-Access-Token`
   - Value: `b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a`
3. **Access URLs**:
   - Prefect: https://everybody-pastor-appearing-tell.trycloudflare.com:4200
   - API: https://everybody-pastor-appearing-tell.trycloudflare.com:8000

---

## Setup Cloudflare Tunnel on Vast.AI

If you need to set it up or restart it:

### Install cloudflared

```bash
# On Vast.AI instance
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Start Tunnel (Background)

```bash
# Create tunnel config
cat > /workspace/tunnel-config.yml <<EOF
url: http://localhost:4200
tunnel: auto
no-autoupdate: true
EOF

# Start tunnel in background
nohup cloudflared tunnel --config /workspace/tunnel-config.yml > /workspace/cloudflared.log 2>&1 &

# Get tunnel URL (wait 5 seconds)
sleep 5
grep -A 1 "https://" /workspace/cloudflared.log | tail -1
```

### Multiple Services

To expose multiple ports:

```bash
# Stop existing tunnel
pkill cloudflared

# Create multi-service config
cat > /workspace/tunnel-config.yml <<EOF
ingress:
  - hostname: everybody-pastor-appearing-tell.trycloudflare.com
    service: http://localhost:4200
  - service: http://localhost:8000
EOF

# Start tunnel
nohup cloudflared tunnel --config /workspace/tunnel-config.yml > /workspace/cloudflared.log 2>&1 &
```

---

## Access Services via Cloudflare

### From Browser

**Prefect UI**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

### From Command Line (curl)

```bash
# Health check
curl -H "CF-Access-Token: b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a" \
  https://everybody-pastor-appearing-tell.trycloudflare.com:8000/healthz

# API request
curl -X POST \
  -H "CF-Access-Token: b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a" \
  -H "Content-Type: application/json" \
  https://everybody-pastor-appearing-tell.trycloudflare.com:8000/api/v1/extraction/queue \
  -d '{"source": "test", "batch_size": 10}'
```

### From Python

```python
import requests

headers = {
    'CF-Access-Token': 'b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a',
    'Content-Type': 'application/json'
}

# Health check
response = requests.get(
    'https://everybody-pastor-appearing-tell.trycloudflare.com:8000/healthz',
    headers=headers
)
print(response.json())

# Queue extraction
response = requests.post(
    'https://everybody-pastor-appearing-tell.trycloudflare.com:8000/api/v1/extraction/queue',
    headers=headers,
    json={'source': 'test', 'batch_size': 10}
)
print(response.json())
```

---

## Docker Deployment with Cloudflare

### Update .env File

```bash
# On Vast.AI instance
nano .env

# Add these lines:
CLOUDFLARE_TUNNEL_URL=https://everybody-pastor-appearing-tell.trycloudflare.com
CLOUDFLARE_TOKEN=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
PUBLIC_URL=https://everybody-pastor-appearing-tell.trycloudflare.com
```

### Deploy with Cloudflare

```bash
# Standard deployment
cd /workspace/BPO-Web

docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu.yml \
  --profile base \
  up -d

# Start cloudflared
nohup cloudflared tunnel --url http://localhost:4200 > /workspace/cloudflared.log 2>&1 &

# Verify tunnel
sleep 5
cat /workspace/cloudflared.log | grep "https://"
```

---

## Advantages Over SSH Tunneling

| Feature | SSH Tunnel | Cloudflare Tunnel |
|---------|-----------|-------------------|
| **Setup** | Complex | Simple |
| **Connection** | Must stay open | Runs in background |
| **HTTPS** | No | Yes |
| **Public Access** | No | Yes |
| **Authentication** | SSH key | Token |
| **Reconnect** | Manual | Automatic |
| **Multiple Users** | Difficult | Easy (share URL) |

---

## Security Considerations

### ✅ Current Setup (Good)

- Token-based authentication
- HTTPS encryption
- Cloudflare DDoS protection
- No exposed ports on Vast.AI

### 🔒 Additional Security (Optional)

#### 1. IP Whitelist

```bash
# Cloudflare Access Rules (requires Cloudflare account)
# Set IP whitelist in Cloudflare dashboard
```

#### 2. API Key Authentication

```python
# Add to your API calls
headers = {
    'CF-Access-Token': 'b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a',
    'X-API-Key': 'your-api-key-here',  # Additional auth
}
```

#### 3. Rotate Token

```bash
# Generate new tunnel (new token)
cloudflared tunnel --url http://localhost:4200

# Update your saved token with new one
```

---

## Monitoring Cloudflare Tunnel

### Check Tunnel Status

```bash
# Check if running
ps aux | grep cloudflared

# View logs
tail -f /workspace/cloudflared.log

# Restart if needed
pkill cloudflared
nohup cloudflared tunnel --url http://localhost:4200 > /workspace/cloudflared.log 2>&1 &
```

### Auto-Restart on Reboot

```bash
# Create systemd service
sudo tee /etc/systemd/system/cloudflared.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:4200
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Troubleshooting

### Tunnel Not Working

```bash
# Check cloudflared is running
ps aux | grep cloudflared

# Restart tunnel
pkill cloudflared
nohup cloudflared tunnel --url http://localhost:4200 > /workspace/cloudflared.log 2>&1 &

# Wait and check logs
sleep 5
cat /workspace/cloudflared.log
```

### Services Not Accessible

```bash
# Check Docker services
docker-compose ps

# Check services are listening
netstat -tlnp | grep -E '4200|8000'

# Restart Docker services
docker-compose restart
```

### 502 Bad Gateway

```bash
# Service not ready yet
docker-compose ps

# Check logs
docker-compose logs prefect-server
docker-compose logs api

# Restart service
docker-compose restart prefect-server
```

---

## Quick Commands

### Access URLs

```bash
# Prefect UI
echo "https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a"

# API
echo "https://everybody-pastor-appearing-tell.trycloudflare.com:8000/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a"

# API Docs
echo "https://everybody-pastor-appearing-tell.trycloudflare.com:8000/docs?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a"
```

### Tunnel Management

```bash
# Start tunnel
nohup cloudflared tunnel --url http://localhost:4200 > /workspace/cloudflared.log 2>&1 &

# Stop tunnel
pkill cloudflared

# Check status
ps aux | grep cloudflared

# View logs
tail -f /workspace/cloudflared.log
```

---

## Integration with API Clients

### JavaScript/Node.js

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://everybody-pastor-appearing-tell.trycloudflare.com:8000',
  headers: {
    'CF-Access-Token': 'b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a'
  }
});

// Queue extraction
api.post('/api/v1/extraction/queue', {
  source: 'test',
  batch_size: 10
}).then(response => {
  console.log(response.data);
});
```

### Python

```python
import requests

class BPOClient:
    def __init__(self):
        self.base_url = 'https://everybody-pastor-appearing-tell.trycloudflare.com:8000'
        self.headers = {
            'CF-Access-Token': 'b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a'
        }

    def queue_extraction(self, source, batch_size=100):
        response = requests.post(
            f'{self.base_url}/api/v1/extraction/queue',
            headers=self.headers,
            json={'source': source, 'batch_size': batch_size}
        )
        return response.json()

# Usage
client = BPOClient()
result = client.queue_extraction('test_data')
print(result)
```

---

## Summary

### ✅ You Have Public Access!

Your services are now accessible from anywhere via:
- **URL**: https://everybody-pastor-appearing-tell.trycloudflare.com
- **Token**: `b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a`

### 🎯 Quick Access

**Prefect UI**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

**API**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:8000/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

### 📝 No SSH Tunnel Needed!

- Access from any device
- HTTPS encryption
- Share with team easily
- Auto-reconnects

---

**Your services are now publicly accessible with secure authentication! 🚀**

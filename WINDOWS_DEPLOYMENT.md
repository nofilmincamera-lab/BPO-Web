# Windows PowerShell Deployment Guide

## You're on Windows - Different Commands Needed!

This guide is specifically for **Windows PowerShell** users deploying to Vast.AI.

---

## Issue 1: SSH Permission Denied

You need to set up SSH key authentication with Vast.AI.

### Fix SSH Access

```powershell
# 1. Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location (C:\Users\YourName\.ssh\id_ed25519)
# Press Enter twice for no passphrase

# 2. Copy your public key
Get-Content ~\.ssh\id_ed25519.pub | clip
# This copies your public key to clipboard

# 3. Add to Vast.AI
# Go to: https://cloud.vast.ai/account/
# Click "Change SSH Key"
# Paste your key (already in clipboard)
# Click "SET SSH KEY"

# 4. Wait 30 seconds, then try connecting
Start-Sleep -Seconds 30

# 5. Connect to Vast.AI (single line - no backslashes!)
ssh -p 40731 root@198.53.64.194
```

---

## Issue 2: PowerShell Multi-Line Commands

PowerShell uses **backticks (`)** not backslashes for line continuation:

### ❌ WRONG (Bash syntax)
```bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu.yml \
  --profile base \
  up -d
```

### ✅ CORRECT (PowerShell syntax)
```powershell
docker-compose `
  -f docker-compose.yml `
  -f docker-compose.vastai-gpu.yml `
  --profile base `
  up -d
```

### ✅ BETTER (Single line)
```powershell
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d
```

---

## Issue 3: Container Name Conflicts

You have containers already running. Clean them up first:

```powershell
# Stop all containers
docker-compose down

# Remove all containers (force)
docker rm -f $(docker ps -aq)

# Clean up networks
docker network prune -f

# Clean up volumes (CAREFUL - deletes data!)
docker volume prune -f
```

---

## Complete Windows Deployment Steps

### Step 1: Setup SSH Key

```powershell
# Generate key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to clipboard
Get-Content ~\.ssh\id_ed25519.pub | clip

# Add to Vast.AI (paste from clipboard)
# https://cloud.vast.ai/account/ → Change SSH Key

# Wait 30 seconds
Start-Sleep -Seconds 30
```

### Step 2: Connect to Vast.AI

```powershell
# Connect (single line!)
ssh -p 40731 root@198.53.64.194

# You should now be on the Vast.AI instance (Linux)
```

### Step 3: On Vast.AI Instance (Linux Commands)

```bash
# Now you're on Linux, use Linux commands

# Navigate to workspace
cd /workspace

# Clone repository
git clone https://github.com/nofilmincamera-lab/BPO-Web.git
cd BPO-Web

# Checkout branch
git checkout claude/repo-audit-setup-011CUprP7imMTf57g4GGoLVQ
git pull

# Setup environment
cp .env.example .env
nano .env
# Change DB_PASSWORD to something secure
# Save: Ctrl+X, Y, Enter

# Create secrets
mkdir -p ops/secrets
echo "your_secure_password" > ops/secrets/postgres_password.txt
chmod 600 ops/secrets/postgres_password.txt

# Create networks
docker network create bpo-main-network
docker network create bpo-gpu-network
docker network create bpo-db-network
docker network create bpo-monitoring-network
docker network create bpo-external-network

# Deploy (single line)
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d

# Wait
sleep 60

# Check status
docker-compose ps

# Verify GPU
nvidia-smi
```

### Step 4: Access Services

Since you have Cloudflare Tunnel, just open in browser:

**Prefect UI**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

**API**:
```
https://everybody-pastor-appearing-tell.trycloudflare.com:8000/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

---

## Windows PowerShell Quick Reference

### Line Continuation

```powershell
# Use backticks (`)
$command = docker-compose `
  -f file1.yml `
  -f file2.yml `
  up -d

# Or just use one line
docker-compose -f file1.yml -f file2.yml up -d
```

### Copy to Clipboard

```powershell
# Copy file content
Get-Content file.txt | clip

# Copy command output
docker ps | clip
```

### Sleep/Wait

```powershell
# Wait 60 seconds
Start-Sleep -Seconds 60
```

### List Files

```powershell
# List files
Get-ChildItem
# Or use alias
ls
dir
```

### Change Directory

```powershell
# Change directory
Set-Location D:\BPO-Project
# Or use alias
cd D:\BPO-Project
```

---

## Fix Your Current Local Windows Setup

You also have issues with your local D:\BPO-Project. Here's how to fix:

### Clean Up Local Docker

```powershell
# Navigate to your project
cd D:\BPO-Project

# Stop everything
docker-compose down

# Remove conflicting containers
docker rm -f bpo-prefect-redis bpo-postgres bpo-prefect-db bpo-pgbouncer

# Start fresh
docker-compose up -d

# Check status
docker-compose ps
```

### Install PostgreSQL Tools (Optional)

If you need `psql` and `pg_dump` on Windows:

```powershell
# Download PostgreSQL installer
# https://www.postgresql.org/download/windows/

# Or use Docker for database commands
docker exec -it bpo-postgres psql -U postgres -d bpo_intel
```

### Install Prefect CLI

```powershell
# Install Prefect
pip install prefect

# Use prefect command
prefect --help

# List work pools
prefect work-pool ls
```

---

## Common Windows PowerShell Errors

### Error: "The term 'psql' is not recognized"

**Solution**: PostgreSQL not installed or not in PATH

```powershell
# Option 1: Install PostgreSQL
# Download from https://www.postgresql.org/download/windows/

# Option 2: Use Docker
docker exec -it bpo-postgres psql -U postgres -d bpo_intel
```

### Error: "Cannot find path '/workspace/BPO-Web'"

**Solution**: `/workspace` is a Linux path, not Windows

```powershell
# On Windows, use:
cd D:\BPO-Project\BPO-Web

# On Vast.AI (Linux), use:
cd /workspace/BPO-Web
```

### Error: "Missing expression after unary operator '--'"

**Solution**: Wrong line continuation character

```powershell
# Wrong (bash)
docker-compose \
  --profile base

# Right (PowerShell)
docker-compose `
  --profile base

# Best (one line)
docker-compose --profile base up -d
```

---

## Your Next Steps (In Order)

### 1. Setup SSH Key (Windows PowerShell)

```powershell
# Generate key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to clipboard
Get-Content ~\.ssh\id_ed25519.pub | clip

# Add to Vast.AI: https://cloud.vast.ai/account/
# Wait 30 seconds
```

### 2. Connect to Vast.AI (Windows PowerShell)

```powershell
ssh -p 40731 root@198.53.64.194
```

### 3. Deploy on Vast.AI (Linux - after SSH)

```bash
cd /workspace
git clone https://github.com/nofilmincamera-lab/BPO-Web.git
cd BPO-Web
git checkout claude/repo-audit-setup-011CUprP7imMTf57g4GGoLVQ

cp .env.example .env
nano .env  # Set DB_PASSWORD

mkdir -p ops/secrets
echo "your_password" > ops/secrets/postgres_password.txt

docker network create bpo-main-network
docker network create bpo-gpu-network
docker network create bpo-db-network
docker network create bpo-monitoring-network
docker network create bpo-external-network

docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d
```

### 4. Access Services (Any browser)

```
https://everybody-pastor-appearing-tell.trycloudflare.com:4200/?token=b859fd36a46f2ba7a33150784ecfcef70590999c7d698072dc42ac989ae8ed7a
```

---

## Troubleshooting

### SSH Still Failing?

```powershell
# Check if key was created
ls ~\.ssh\

# Should see:
# id_ed25519
# id_ed25519.pub

# Display public key
Get-Content ~\.ssh\id_ed25519.pub

# Copy and manually add to Vast.AI
```

### Docker Issues on Windows?

```powershell
# Restart Docker Desktop
# System Tray → Docker → Restart

# Check Docker is running
docker ps

# Check WSL 2 (required for Docker Desktop)
wsl --status
```

---

## Summary

**You're on Windows** → Different syntax needed!

| Command | Linux/Mac | Windows PowerShell |
|---------|-----------|-------------------|
| Line continuation | `\` | `` ` `` |
| Copy to clipboard | `pbcopy` / `xclip` | `clip` |
| Sleep | `sleep 60` | `Start-Sleep -Seconds 60` |
| List files | `ls` | `Get-ChildItem` or `ls` |
| Path separator | `/` | `\` |

**For Vast.AI deployment**:
1. Fix SSH key issue first
2. SSH to Vast.AI (then use Linux commands)
3. Deploy Docker stack
4. Access via Cloudflare URL

**No SSH needed for access** - just use the Cloudflare link!

---

**Start with Step 1 above to fix SSH, then connect to Vast.AI!**

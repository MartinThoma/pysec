# PySec Server-Client Setup Guide

This guide will help you set up the new server-client functionality in pysec.

## Quick Setup

### Step 1: Install Dependencies

```bash
# Make sure you're in the pysec directory
cd /path/to/pysec

# Install the package with all dependencies
pip install -e .
```

### Step 2: Start the Server

```bash
# Start the server (will run on http://127.0.0.1:8000)
pysec server start
```

The server will display:
- Server URL: http://127.0.0.1:8000

### Step 3: Access the Dashboard

1. Open http://127.0.0.1:8000 in your browser
2. Login
3. Click "Add New Client" to create a client
4. Copy the generated token

### Step 4: Configure a Client

On any machine you want to monitor:

```bash
# Configure the client with your server URL and token
pysec client configure \
  --server-url http://your-server-ip:8000 \
  --token YOUR_GENERATED_TOKEN
```

### Step 5: Run Client Audit

```bash
# Run the audit and send data to server
pysec client run
```

## Available Commands

### Server Commands
```bash
# Start server with custom settings
pysec server start --host 0.0.0.0 --port 8080

# Start with auto-reload for development
pysec server start --reload
```

### Client Commands
```bash
# Configure client
pysec client configure --server-url URL --token TOKEN

# Run audit (uses saved config)
pysec client run

# Run with custom server/token (overrides config)
pysec client run --server-url URL --token TOKEN
```

### Existing Commands (still available)
```bash
# Audit system configuration
pysec audit config

# Audit installed packages
pysec audit packages
```

## Features

✅ **Web Dashboard**: Modern admin interface for managing clients
✅ **Client Management**: Generate and manage authentication tokens
✅ **Package Discovery**: Automatically detects pip, dpkg, and rpm packages
✅ **Audit Logging**: Collects system events and login information
✅ **Secure Communication**: Token-based authentication
✅ **Data Visualization**: View client status, logs, and packages
✅ **Cross-Platform**: Works on Linux, macOS, and Windows

## File Locations

- **Server Database**: `${XDG_DATA_HOME}/pysec/pysec.db` (default: `~/.local/share/pysec/pysec.db`)
- **Client Config**: `${XDG_CONFIG_HOME}/pysec/client.json` (default: `~/.config/pysec/client.json`)

## Security Notes

🔒 **Use HTTPS**: Deploy behind a reverse proxy with SSL/TLS in production
🔒 **Network Security**: Restrict server access to authorized networks only

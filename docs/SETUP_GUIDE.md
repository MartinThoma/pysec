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

### Step 2: Initialize the Database

Before starting the server for the first time, you need to set up the database:

```bash
# Apply database migrations
pysec server manage.py migrate

# Create a superuser account for admin access
pysec server manage.py createsuperuser
```

You'll be prompted to enter:
- Username
- Email address (optional)
- Password

**Note**: Remember these credentials - you'll need them to log into the dashboard.

### Step 3: Start the Server

```bash
# Start the server (will run on http://127.0.0.1:8000)
pysec server start
```

The server will display:
- Server URL: http://127.0.0.1:8000

### Step 4: Access the Dashboard

1. Open http://127.0.0.1:8000 in your browser
2. Login with the superuser credentials you created in Step 2
3. Click "Add New Client" to create a client
4. Copy the generated token

### Step 5: Configure a Client

On any machine you want to monitor:

```bash
# Configure the client with your server URL and token
pysec client configure \
  --server-url http://your-server-ip:8000 \
  --token YOUR_GENERATED_TOKEN
```

### Step 6: Run Client Audit

```bash
# Run the audit and send data to server
pysec client run
```

## Available Commands

### Server Commands
```bash
# Initialize database (run once before first start)
pysec server manage.py migrate
pysec server manage.py createsuperuser

# Start server with custom settings
pysec server start --host 0.0.0.0 --port 8080

# Create a client and get authentication token
pysec server manage.py create_client myclient

# Access all Django management commands
pysec server manage.py help
pysec server manage.py collectstatic
pysec server manage.py shell
```

### Django Management Commands

The `pysec server manage.py` command provides full access to Django's management system:

```bash
# See all available commands
pysec server manage.py help

# Common Django commands
pysec server manage.py runserver 0.0.0.0:8000
pysec server manage.py migrate --plan
pysec server manage.py createsuperuser
pysec server manage.py create_client myclient
pysec server manage.py collectstatic
pysec server manage.py shell
pysec server manage.py check
pysec server manage.py showmigrations
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

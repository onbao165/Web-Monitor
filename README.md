# Web Monitor

A web monitoring application that runs as a background daemon on Linux systems.

## Features

**Space Management**
- Create and organize monitoring spaces for different environments (production, staging, etc.)
- Start/stop all monitors in a space with single commands

**Monitor Types**
- **URL Monitoring**: Check website availability, response codes, SSL certificates, content validation
- **Database Monitoring**: Test database connections and availability (PostgreSQL, MySQL, etc.)
- Configurable check intervals, timeouts, and retry logic

**Notification System**
- Email alerts for monitor failures and recoveries
- Configurable SMTP settings
- Health alerts with customizable thresholds and check intervals
- Space-specific notification email lists

**Data Management**
- Automatic result storage with configurable retention policies
- Separate retention for healthy vs unhealthy results
- Data cleanup jobs to manage storage usage
- Export/import functionality for spaces and monitors

**System Integration**
- Background daemon operation with systemd service
- Comprehensive CLI interface for all operations
- YAML-based configuration for easy automation

## Prerequisites

- Linux system with systemd
- Python 3.x
- Root/sudo access for installation

## Installation

### Automated Installation

The easiest way to install Web Monitor is using the provided installation script:

```bash
# Clone the repository
git clone https://github.com/onbao165/Web-Monitor.git
cd Web-Monitor

# Run the installation script (requires sudo)
sudo ./scripts/install.sh
```

### Manual Installation Steps

If you prefer to install manually, follow these steps:

#### 1. System Requirements Check

Ensure Python 3 is installed:
```bash
python3 --version
```

#### 2. Create System User

Create a dedicated system user for the service:
```bash
sudo useradd --system --home-dir /opt/webmonitor --shell /bin/false webmonitor
```

#### 3. Create Directories

Set up the required directory structure:
```bash
sudo mkdir -p /opt/webmonitor          # Application code
sudo mkdir -p /var/lib/webmonitor      # Database and persistent data
sudo mkdir -p /var/run/webmonitor      # Socket files and runtime data
sudo mkdir -p /var/log/webmonitor      # Log files

# Set ownership
sudo chown -R webmonitor:webmonitor /opt/webmonitor
sudo chown -R webmonitor:webmonitor /var/lib/webmonitor
sudo chown -R webmonitor:webmonitor /var/run/webmonitor
sudo chown -R webmonitor:webmonitor /var/log/webmonitor
```

#### 4. Install Application

Copy the application files and set up the Python environment:
```bash
# Copy application files
sudo cp -r . /opt/webmonitor/
cd /opt/webmonitor

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R webmonitor:webmonitor venv

# Install dependencies
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -e .
```

#### 5. Install Systemd Service

Register the service with systemd:
```bash
sudo cp systemd/webmonitor.service /etc/systemd/system/
sudo systemctl daemon-reload
```

#### 6. Set Up CLI Access

Create a symbolic link for global CLI access:
```bash
sudo ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/webmonitor
sudo ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/wm
```

## Service Management

### Enable Auto-Start on Boot

```bash
sudo systemctl enable webmonitor.service
```

### Start the Service

```bash
sudo systemctl start webmonitor
```

### Check Service Status

```bash
sudo systemctl status webmonitor
```

### Stop the Service

```bash
sudo systemctl stop webmonitor
```

### View Logs

```bash
# View recent logs
sudo journalctl -u webmonitor

# Follow logs in real-time
sudo journalctl -u webmonitor -f
```

## CLI Usage

After installation, you can use the `webmonitor` command globally:

```bash
# Initialize configuration (run this first)
webmonitor init

# View available commands
webmonitor --help

# Example commands (replace with actual CLI commands)
webmonitor status
webmonitor config
```

## Configuration

The application stores its configuration and data in:
- Configuration: `/var/lib/webmonitor/`
- Logs: `/var/log/webmonitor/`
- Runtime data: `/var/run/webmonitor/`

### CLI Command Not Found

If the `webmonitor` command is not found after installation:

1. Check if the symlink exists:
   ```bash
   ls -la /usr/local/bin/webmonitor
   ls -la /usr/local/bin/wm
   ```

2. Recreate the symlink:
   ```bash
   sudo ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/webmonitor
   sudo ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/wm
   ```

## Uninstallation

To remove Web Monitor, use the provided uninstall script:

```bash
# Complete removal (removes all data and configuration)
sudo ./scripts/uninstall.sh

# Preserve configuration files
sudo ./scripts/uninstall.sh --preserve-config

# Preserve data files (creates backup)
sudo ./scripts/uninstall.sh --preserve-data

# Preserve both configuration and data
sudo ./scripts/uninstall.sh --preserve-config --preserve-data
```

The uninstall script will:
- Stop and disable the systemd service
- Remove the CLI symlink
- Remove application files
- Remove system user and group
- Optionally preserve or backup configuration and data files

#!/bin/bash
set -e

echo "🚀 Installing Web Monitor as a systemd service..."

# Must run as root to create users and install system services
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Python 3 is required to run the application
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   You can install it with 'sudo apt-get install python3'"
    exit 1
fi

# Python venv is required to isolate dependencies
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Python venv is required but not installed"
    echo "   You can install it with 'sudo apt-get install python3-venv'"
    exit 1
fi

echo "✅ System checks passed"

# Create dedicated user
echo "👤 Creating system user..."
if ! getent passwd webmonitor > /dev/null 2>&1; then
    useradd --system --home-dir /opt/webmonitor --shell /bin/false webmonitor
    echo "✅ Created user: webmonitor"
else
    echo "ℹ️  User webmonitor already exists"
fi

# Standard Linux directories for applications
echo "📁 Creating directories..."
mkdir -p /opt/webmonitor          # Application code goes here
mkdir -p /var/lib/webmonitor      # Database and persistent data
mkdir -p /var/run/webmonitor      # Socket files and runtime data
mkdir -p /var/log/webmonitor      # Log files

# Make sure webmonitor user owns its directories
chown -R webmonitor:webmonitor /opt/webmonitor
chown -R webmonitor:webmonitor /var/lib/webmonitor
chown -R webmonitor:webmonitor /var/run/webmonitor
chown -R webmonitor:webmonitor /var/log/webmonitor

echo "✅ Directories created"

# Copy application files to system location
echo "📦 Installing application..."
cp -r . /opt/webmonitor/
cd /opt/webmonitor

# Isolated Python environment prevents conflicts
echo "🐍 Setting up Python environment..."
python3 -m venv venv
chown -R webmonitor:webmonitor venv

# Install the application and its dependencies
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -e .

echo "✅ Python environment ready"

# Register with systemd so it can manage the service
echo "⚙️  Installing systemd service..."
cp systemd/webmonitor.service /etc/systemd/system/
systemctl daemon-reload

# Set up symlink for cli tool
echo "🔗 Setting up CLI shortcuts..."
ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/webmonitor
ln -sf /opt/webmonitor/venv/bin/webmonitor /usr/local/bin/wm

echo "🎉 Installation complete!"
echo ""
echo "You can now use the CLI with either 'webmonitor' or the shorthand 'wm'"
echo ""
echo "To enable the service to start on boot:"
echo "  sudo systemctl enable webmonitor.service"
echo ""
echo "To start your service:"
echo "  sudo systemctl start webmonitor"
echo ""
echo "To check if it's running:"
echo "  sudo systemctl status webmonitor"
echo ""
echo "To see logs:"
echo "  sudo journalctl -u webmonitor -f"



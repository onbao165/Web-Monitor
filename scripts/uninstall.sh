#!/bin/bash
set -e

# Web Monitor Uninstallation Script
# This script removes Web Monitor service and files

INSTALL_DIR="/opt/webmonitor"
CONFIG_DIR="/etc/webmonitor"
DATA_DIR="/var/lib/webmonitor"
LOG_DIR="/var/log/webmonitor"
RUN_DIR="/var/run/webmonitor"
SERVICE_USER="webmonitor"
SERVICE_GROUP="webmonitor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Stop and disable service
remove_service() {
    log_info "Stopping and removing systemd service..."
    
    if systemctl is-active --quiet webmonitor.service; then
        systemctl stop webmonitor.service
        log_info "Service stopped"
    fi
    
    if systemctl is-enabled --quiet webmonitor.service 2>/dev/null; then
        systemctl disable webmonitor.service
        log_info "Service disabled"
    fi
    
    if [[ -f /etc/systemd/system/webmonitor.service ]]; then
        rm -f /etc/systemd/system/webmonitor.service
        systemctl daemon-reload
        log_info "Service file removed"
    fi
    
    log_success "Service removed"
}

# Backup data
backup_data() {
    if [[ "$PRESERVE_DATA" == "yes" ]]; then
        log_info "Backing up data..."
        BACKUP_DIR="/tmp/webmonitor-backup-$(date +%Y%m%d%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        if [[ -d "$DATA_DIR" ]]; then
            cp -r "$DATA_DIR" "$BACKUP_DIR/"
            log_info "Data backed up to $BACKUP_DIR"
        fi
        
        if [[ -d "$CONFIG_DIR" ]]; then
            cp -r "$CONFIG_DIR" "$BACKUP_DIR/"
            log_info "Configuration backed up to $BACKUP_DIR"
        fi
        
        log_success "Backup completed to $BACKUP_DIR"
    fi
}

# Remove files
remove_files() {
    log_info "Removing files..."
    
    # Remove installation directory
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_info "Installation directory removed"
    fi
    
    # Remove configuration
    if [[ -d "$CONFIG_DIR" ]]; then
        if [[ "$PRESERVE_CONFIG" == "yes" ]]; then
            log_info "Preserving configuration directory"
        else
            rm -rf "$CONFIG_DIR"
            log_info "Configuration directory removed"
        fi
    fi
    
    # Remove data
    if [[ -d "$DATA_DIR" ]]; then
        if [[ "$PRESERVE_DATA" == "yes" ]]; then
            log_info "Preserving data directory"
        else
            rm -rf "$DATA_DIR"
            log_info "Data directory removed"
        fi
    fi
    
    # Remove logs
    if [[ -d "$LOG_DIR" ]]; then
        rm -rf "$LOG_DIR"
        log_info "Log directory removed"
    fi
    
    # Remove run directory
    if [[ -d "$RUN_DIR" ]]; then
        rm -rf "$RUN_DIR"
        log_info "Run directory removed"
    fi
    
    log_success "Files removed"
}

# Remove user and group
remove_user() {
    log_info "Removing system user and group..."
    
    if getent passwd "$SERVICE_USER" > /dev/null 2>&1; then
        userdel "$SERVICE_USER"
        log_info "User $SERVICE_USER removed"
    fi
    
    if getent group "$SERVICE_GROUP" > /dev/null 2>&1; then
        groupdel "$SERVICE_GROUP"
        log_info "Group $SERVICE_GROUP removed"
    fi
    
    log_success "User and group removed"
}

# Show help
show_help() {
    echo "Web Monitor Uninstallation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --preserve-config    Keep configuration files"
    echo "  --preserve-data      Keep data files and create backup"
    echo "  --help               Show this help message"
    echo ""
}

# Parse command line arguments
parse_args() {
    PRESERVE_CONFIG="no"
    PRESERVE_DATA="no"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --preserve-config)
                PRESERVE_CONFIG="yes"
                shift
                ;;
            --preserve-data)
                PRESERVE_DATA="yes"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Remove CLI symlinks
remove_cli_symlinks() {
    log_info "Removing CLI symlinks..."
    if [[ -L /usr/local/bin/webmonitor ]]; then
        rm -f /usr/local/bin/webmonitor
        log_info "Main CLI symlink removed"
    fi
    if [[ -L /usr/local/bin/wm ]]; then
        rm -f /usr/local/bin/wm
        log_info "Shorthand CLI symlink removed"
    fi
    log_success "CLI symlinks removed"
}

# Main uninstallation function
main() {
    parse_args "$@"
    
    log_info "Starting Web Monitor uninstallation..."
    
    check_root
    remove_service
    backup_data
    remove_files
    remove_user
    remove_cli_symlinks
    
    log_success "Web Monitor uninstallation completed!"
}

# Run main function
main "$@"


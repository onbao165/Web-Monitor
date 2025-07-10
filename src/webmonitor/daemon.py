import socket
import json
import threading
import os
import time
import signal
import sys
import logging
import logging.handlers
import configparser
from pathlib import Path
from .infrastructure import Database
from .services import MonitorScheduler
from .api import CommandHandler
from concurrent.futures import ThreadPoolExecutor

class WebMonitorDaemon:
    def __init__(self, config_file=None):
        self.running = True
        self.config_file = config_file or os.getenv('WEBMONITOR_CONFIG', '/etc/webmonitor/webmonitor.conf')

        # Load configuration
        self.config = self._load_config()

        # Set up paths
        self.socket_path = os.getenv('SOCKET_PATH', self.config.get('daemon', 'socket_path', fallback='/tmp/webmonitor.sock'))
        self.pid_file = self.config.get('daemon', 'pid_file', fallback='/var/run/webmonitor/webmonitor.pid')
        self.data_dir = os.getenv('WEBMONITOR_DATA_DIR', '/var/lib/webmonitor')
        self.log_dir = os.getenv('WEBMONITOR_LOG_DIR', '/var/log/webmonitor')

        # Ensure directories exist
        self._ensure_directories()

        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger("WebMonitorDaemon")
        
        # Initialize database and scheduler
        self.database = Database()
        self.database.init_db()
        self.scheduler = MonitorScheduler(self.database)

        # Initialize email service
        self._initialize_email_service()

        # Initialize command handler
        self.command_handler = CommandHandler(self.database, self.scheduler)

        # Add a thread pool for handling connections
        max_workers = self.config.getint('daemon', 'max_workers', fallback=10)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # Write PID file
        self._write_pid_file()

    def _load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        return config

    def _ensure_directories(self):
        directories = [
            os.path.dirname(self.socket_path),
            os.path.dirname(self.pid_file),
            self.data_dir,
            self.log_dir
        ]

        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, mode=0o755, exist_ok=True)

    def _setup_logging(self):
        log_level = getattr(logging, self.config.get('logging', 'log_level', fallback='INFO').upper())
        log_format = self.config.get('logging', 'log_format',
                                   fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Create formatter
        formatter = logging.Formatter(log_format)

        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove default handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add file handler with rotation
        log_file = os.path.join(self.log_dir, self.config.get('logging', 'log_file', fallback='webmonitor.log'))
        max_bytes = self._parse_size(self.config.get('logging', 'max_log_size', fallback='10MB'))
        backup_count = self.config.getint('logging', 'backup_count', fallback=5)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Add console handler for systemd
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    def _parse_size(self, size_str):
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def _write_pid_file(self):
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"Warning: Could not write PID file {self.pid_file}: {e}")

    def _remove_pid_file(self):
        try:
            if os.path.exists(self.pid_file):
                os.unlink(self.pid_file)
        except Exception as e:
            self.logger.warning(f"Could not remove PID file {self.pid_file}: {e}")

    def _initialize_email_service(self):
        try:
            from .services.email_service import get_email_service
            from .config import get_config_manager

            config_manager = get_config_manager()
            email_service = get_email_service()

            if config_manager.is_email_configured():
                self.logger.info("Email service configured and ready")
            else:
                self.logger.warning("Email service not configured - notifications will be disabled")
                self.logger.info("Run 'webmonitor email configure' to set up email notifications")

        except Exception as e:
            self.logger.error(f"Failed to initialize email service: {e}")

    def handle_command(self, command_data):
        try:
            cmd = json.loads(command_data)
            return self.command_handler.handle_command(cmd)
        except Exception as e:
            self.logger.error(f"Error handling command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def start_socket_server(self):
        self._start_unix_socket_server()
    
    def _start_unix_socket_server(self):
        # Remove existing socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.settimeout(1.0)  # Add timeout to allow checking self.running
        
        # Set socket permissions so user can access it
        os.chmod(self.socket_path, 0o666)
        
        sock.listen(5)
        
        self.logger.info(f"Unix socket server started at {self.socket_path}")
        
        while self.running:
            try:
                conn, addr = sock.accept()
                # Handle connection in thread pool instead of blocking
                self.thread_pool.submit(self._handle_connection, conn)
            except socket.timeout:
                # This is expected due to the timeout we set
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Socket error: {str(e)}", exc_info=True)
                    
        sock.close()
        self.thread_pool.shutdown(wait=False)
    
    def _handle_connection(self, conn):
        try:
            data = conn.recv(4096).decode()
            response = self.handle_command(data)
            conn.send(json.dumps(response).encode())
            conn.close()
        except Exception as e:
            self.logger.error(f"Error handling connection: {str(e)}", exc_info=True)
            try:
                conn.send(json.dumps({'status': 'error', 'message': str(e)}).encode())
                conn.close()
            except:
                pass
    
    def signal_handler(self, signum, frame):
        signal_names = {signal.SIGTERM: 'SIGTERM', signal.SIGINT: 'SIGINT', signal.SIGHUP: 'SIGHUP'}
        signal_name = signal_names.get(signum, str(signum))

        if signum == signal.SIGHUP:
            self.logger.info("Received SIGHUP, reloading configuration...")
            self._reload_config()
        else:
            self.logger.info(f"Received {signal_name}, shutting down gracefully...")
            self.running = False
            self.scheduler.stop()
            self._cleanup()

    def _reload_config(self):
        try:
            self.config = self._load_config()
            self.logger.info("Configuration reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")

    def _cleanup(self):
        try:
            # Remove socket file
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)

            # Remove PID file
            self._remove_pid_file()

            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)

            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
    def start(self):
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)

        # Start socket server in background thread
        socket_thread = threading.Thread(target=self.start_socket_server)
        socket_thread.daemon = True
        socket_thread.start()

        self.logger.info(f"WebMonitor daemon started (PID: {os.getpid()})")

        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

def main():
    try:
        # Get config file from command line if provided
        config_file = None
        if len(sys.argv) > 1:
            config_file = sys.argv[1]

        # Create and start daemon
        daemon = WebMonitorDaemon(config_file)
        daemon.start()
    except Exception as e:
        logging.error(f"Failed to start daemon: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()




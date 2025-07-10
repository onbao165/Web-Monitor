import socket
import json
import threading
import os
import time
import signal
import sys
import logging
from .infrastructure import Database
from .services import MonitorScheduler
from .api import CommandHandler
from concurrent.futures import ThreadPoolExecutor

class WebMonitorDaemon:
    def __init__(self):
        self.running = True
        self.socket_path = os.getenv('SOCKET_PATH', '/tmp/webmonitor.sock')
        self.socket_port = int(os.getenv('SOCKET_PORT', '9000'))
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
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
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _initialize_email_service(self):
        """Initialize email service with configuration."""
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
        # Handle shutdown signals
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.scheduler.stop()
        
    def start(self):
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Start socket server in background thread
        socket_thread = threading.Thread(target=self.start_socket_server)
        socket_thread.daemon = True
        socket_thread.start()
        
        self.logger.info("WebMonitor daemon started")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        
        # Cleanup
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

def main():
    daemon = WebMonitorDaemon()
    daemon.start()

if __name__ == "__main__":
    main()




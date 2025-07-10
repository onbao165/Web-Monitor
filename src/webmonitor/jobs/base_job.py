import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseJob(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"jobs.{name}")
        self.last_run: datetime = None
        self.run_count: int = 0
        self.error_count: int = 0
    
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    def run(self) -> bool:
        try:
            self.logger.info(f"Starting job: {self.name}")
            start_time = datetime.now()
            
            success = self.execute()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.last_run = end_time
            self.run_count += 1
            
            if success:
                self.logger.info(f"Job {self.name} completed successfully in {duration:.2f}s")
            else:
                self.error_count += 1
                self.logger.warning(f"Job {self.name} completed with errors in {duration:.2f}s")
            
            return success
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Job {self.name} failed with exception: {str(e)}", exc_info=True)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'run_count': self.run_count,
            'error_count': self.error_count,
            'success_rate': (self.run_count - self.error_count) / self.run_count if self.run_count > 0 else 0
        }

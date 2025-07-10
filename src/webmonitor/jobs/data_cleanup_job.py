from typing import Dict, Any
from datetime import datetime
from .base_job import BaseJob
from webmonitor.infrastructure import Database
from webmonitor.config import get_config_manager

class DataCleanupJob(BaseJob):
    def __init__(self, database: Database):
        super().__init__("data_cleanup")
        self.database = database
        self.config_manager = get_config_manager()
    
    def execute(self) -> bool:
        try:
            # Get data cleanup configuration
            cleanup_config = self.config_manager.get_data_cleanup_config()
            
            if not cleanup_config.get('enabled', True):
                self.logger.info("Data cleanup is disabled")
                return True
            
            keep_healthy_days = cleanup_config.get('keep_healthy_results_days', 7)
            keep_unhealthy_days = cleanup_config.get('keep_unhealthy_results_days', 30)
            
            # Safety check: Don't allow cleanup of very recent data
            if keep_healthy_days < 1:
                self.logger.warning("keep_healthy_results_days must be at least 1, using default of 7")
                keep_healthy_days = 7
            
            if keep_unhealthy_days < 1:
                self.logger.warning("keep_unhealthy_results_days must be at least 1, using default of 30")
                keep_unhealthy_days = 30
            
            # Get preview of what will be deleted
            preview = self.database.get_cleanup_preview(keep_healthy_days, keep_unhealthy_days)
            
            # Log preview information
            self.logger.info(f"Cleanup preview: {preview['total_to_delete']} results will be deleted")
            self.logger.info(f"  - Healthy results (>{keep_healthy_days} days): {preview['healthy_to_delete']}")
            self.logger.info(f"  - Unhealthy results (>{keep_unhealthy_days} days): {preview['unhealthy_to_delete']}")
            self.logger.info(f"  - Total results before cleanup: {preview['total_results']}")
            self.logger.info(f"  - Results remaining after cleanup: {preview['retention_after_cleanup']}")
            
            # Skip cleanup if nothing to delete
            if preview['total_to_delete'] == 0:
                self.logger.info("No old results found to cleanup")
                return True
            
            # Safety check: Don't delete more than 90% of all data in one run
            if preview['total_results'] > 0:
                deletion_percentage = (preview['total_to_delete'] / preview['total_results']) * 100
                if deletion_percentage > 90:
                    self.logger.error(f"Safety check failed: Would delete {deletion_percentage:.1f}% of all data. Aborting cleanup.")
                    return False
            
            # Perform the cleanup
            self.logger.info("Starting data cleanup operation...")
            cleanup_stats = self.database.cleanup_old_results(
                keep_healthy_days=keep_healthy_days,
                keep_unhealthy_days=keep_unhealthy_days,
                batch_size=1000  # Process in batches to avoid long locks
            )
            
            # Log cleanup results
            self._log_cleanup_results(cleanup_stats, keep_healthy_days, keep_unhealthy_days)
            
            # Check for errors
            if cleanup_stats.get('errors'):
                self.logger.error(f"Cleanup completed with errors: {cleanup_stats['errors']}")
                return False
            
            self.logger.info("Data cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Data cleanup job failed: {str(e)}", exc_info=True)
            return False
    
    def _log_cleanup_results(self, stats: Dict[str, Any], keep_healthy_days: int, keep_unhealthy_days: int) -> None:
        """Log detailed cleanup results."""
        duration = stats.get('duration_seconds', 0)
        
        self.logger.info("=" * 50)
        self.logger.info("DATA CLEANUP RESULTS")
        self.logger.info("=" * 50)
        self.logger.info(f"Retention Policy:")
        self.logger.info(f"  - Keep healthy results: {keep_healthy_days} days")
        self.logger.info(f"  - Keep unhealthy results: {keep_unhealthy_days} days")
        self.logger.info(f"")
        self.logger.info(f"Results Deleted:")
        self.logger.info(f"  - Healthy results: {stats.get('healthy_deleted', 0):,}")
        self.logger.info(f"  - Unhealthy results: {stats.get('unhealthy_deleted', 0):,}")
        self.logger.info(f"  - Total deleted: {stats.get('total_deleted', 0):,}")
        self.logger.info(f"")
        self.logger.info(f"Performance:")
        self.logger.info(f"  - Duration: {duration:.2f} seconds")
        self.logger.info(f"  - Batches processed: {stats.get('batches_processed', 0)}")
        if duration > 0 and stats.get('total_deleted', 0) > 0:
            rate = stats['total_deleted'] / duration
            self.logger.info(f"  - Deletion rate: {rate:.0f} records/second")
        self.logger.info("=" * 50)
    
    def get_cleanup_preview(self) -> Dict[str, Any]:
        """Get a preview of what would be cleaned up without actually doing it."""
        cleanup_config = self.config_manager.get_data_cleanup_config()
        keep_healthy_days = cleanup_config.get('keep_healthy_results_days', 7)
        keep_unhealthy_days = cleanup_config.get('keep_unhealthy_results_days', 30)
        
        return self.database.get_cleanup_preview(keep_healthy_days, keep_unhealthy_days)

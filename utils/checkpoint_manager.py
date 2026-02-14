"""
Checkpoint manager for saving and resuming long-running operations
"""
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage checkpoints for resumable operations"""
    
    def __init__(self, checkpoint_dir="checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        logger.info(f"CheckpointManager initialized: {self.checkpoint_dir}")
    
    def save_checkpoint(self, operation_id, data, metadata=None):
        """
        Save a checkpoint for an operation
        
        Args:
            operation_id: Unique identifier for the operation
            data: Data to save (must be serializable)
            metadata: Optional metadata dictionary
        
        Returns:
            Path to checkpoint file
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"
            
            checkpoint = {
                'operation_id': operation_id,
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'metadata': metadata or {}
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, default=str)
            logger.info(f"Checkpoint saved: {checkpoint_file}")
            
            return checkpoint_file
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {str(e)}")
            return None
    
    def load_checkpoint(self, operation_id):
        """
        Load a checkpoint for an operation
        
        Args:
            operation_id: Unique identifier for the operation
        
        Returns:
            Checkpoint data or None if not found
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"
            
            if not checkpoint_file.exists():
                logger.debug(f"No checkpoint found for: {operation_id}")
                return None
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            logger.info(f"Checkpoint loaded: {checkpoint_file}")
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {str(e)}")
            return None
    
    def delete_checkpoint(self, operation_id):
        """
        Delete a checkpoint
        
        Args:
            operation_id: Unique identifier for the operation
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"
            
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                logger.info(f"Checkpoint deleted: {checkpoint_file}")
                return True
            else:
                logger.debug(f"No checkpoint to delete: {operation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting checkpoint: {str(e)}")
            return False
    
    def list_checkpoints(self):
        """
        List all available checkpoints
        
        Returns:
            List of checkpoint information dictionaries
        """
        try:
            checkpoints = []
            
            for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
                try:
                    # Try to load minimal info
                    operation_id = checkpoint_file.stem
                    
                    # Get file modification time
                    mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                    
                    checkpoints.append({
                        'operation_id': operation_id,
                        'file': str(checkpoint_file),
                        'modified': mtime.isoformat(),
                        'size_bytes': checkpoint_file.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Error reading checkpoint {checkpoint_file}: {str(e)}")
            
            return sorted(checkpoints, key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}")
            return []
    
    def cleanup_old_checkpoints(self, max_age_days=7):
        """
        Delete checkpoints older than specified days
        
        Args:
            max_age_days: Maximum age in days
        
        Returns:
            Number of checkpoints deleted
        """
        try:
            deleted_count = 0
            now = datetime.now()
            
            for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint"):
                try:
                    mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                    age_days = (now - mtime).days
                    
                    if age_days > max_age_days:
                        checkpoint_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old checkpoint ({age_days} days): {checkpoint_file}")
                        
                except Exception as e:
                    logger.warning(f"Error deleting checkpoint {checkpoint_file}: {str(e)}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old checkpoints")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up checkpoints: {str(e)}")
            return 0
    
    def get_checkpoint_info(self, operation_id):
        """
        Get information about a checkpoint without loading full data
        
        Args:
            operation_id: Unique identifier for the operation
        
        Returns:
            Dictionary with checkpoint info or None
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{operation_id}.checkpoint"
            
            if not checkpoint_file.exists():
                return None
            
            stat = checkpoint_file.stat()
            
            return {
                'operation_id': operation_id,
                'file': str(checkpoint_file),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"Error getting checkpoint info: {str(e)}")
            return None

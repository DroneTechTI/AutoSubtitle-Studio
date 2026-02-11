"""
Smart synchronization with learning capabilities
"""
import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class SmartSync:
    """Intelligent sync with learning and calibration"""
    
    def __init__(self, calibration_file="sync_calibration.json"):
        self.calibration_file = Path(calibration_file)
        self.calibration_data = self._load_calibration()
    
    def _load_calibration(self):
        """Load calibration data from previous syncs"""
        if self.calibration_file.exists():
            try:
                with open(self.calibration_file, 'r') as f:
                    return json.load(f)
            except:
                return {'corrections': [], 'avg_correction': 0.0}
        return {'corrections': [], 'avg_correction': 0.0}
    
    def _save_calibration(self):
        """Save calibration data"""
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving calibration: {str(e)}")
    
    def learn_from_correction(self, auto_offset, user_offset, video_type='movie'):
        """
        Learn from user correction
        
        Args:
            auto_offset: What auto-sync calculated
            user_offset: What user actually needed
            video_type: Type of content (movie, tv, documentary, etc.)
        """
        correction = user_offset - auto_offset
        
        correction_entry = {
            'auto': auto_offset,
            'user': user_offset,
            'correction': correction,
            'type': video_type
        }
        
        self.calibration_data['corrections'].append(correction_entry)
        
        # Keep only last 50 corrections
        if len(self.calibration_data['corrections']) > 50:
            self.calibration_data['corrections'] = self.calibration_data['corrections'][-50:]
        
        # Calculate average correction
        corrections = [c['correction'] for c in self.calibration_data['corrections']]
        self.calibration_data['avg_correction'] = np.mean(corrections)
        
        self._save_calibration()
        
        logger.info(f"Learned: auto={auto_offset:.2f}s, user={user_offset:.2f}s, correction={correction:.2f}s")
        logger.info(f"Average correction now: {self.calibration_data['avg_correction']:.2f}s")
    
    def apply_calibration(self, auto_offset, video_type='movie'):
        """
        Apply learned calibration to auto-sync result
        
        Args:
            auto_offset: Raw offset from auto-sync
            video_type: Type of content
        
        Returns:
            Calibrated offset
        """
        if not self.calibration_data['corrections']:
            return auto_offset
        
        # Filter corrections by type if available
        type_corrections = [
            c['correction'] for c in self.calibration_data['corrections']
            if c['type'] == video_type
        ]
        
        if type_corrections:
            avg_correction = np.mean(type_corrections)
            logger.info(f"Using type-specific correction for '{video_type}': {avg_correction:.2f}s")
        else:
            avg_correction = self.calibration_data['avg_correction']
            logger.info(f"Using global correction: {avg_correction:.2f}s")
        
        calibrated_offset = auto_offset + avg_correction
        
        logger.info(f"Calibrated offset: {auto_offset:.2f}s → {calibrated_offset:.2f}s")
        
        return calibrated_offset
    
    def get_statistics(self):
        """Get calibration statistics"""
        if not self.calibration_data['corrections']:
            return "Nessun dato di calibrazione disponibile"
        
        corrections = [c['correction'] for c in self.calibration_data['corrections']]
        
        stats = {
            'total_corrections': len(corrections),
            'avg_correction': np.mean(corrections),
            'std_correction': np.std(corrections),
            'min_correction': np.min(corrections),
            'max_correction': np.max(corrections)
        }
        
        return stats
    
    def suggest_offset_adjustment(self, auto_offset):
        """
        Suggest if user should adjust based on patterns
        
        Args:
            auto_offset: Calculated offset
        
        Returns:
            Tuple of (should_adjust, suggested_adjustment, confidence)
        """
        if len(self.calibration_data['corrections']) < 3:
            return False, 0.0, 0.0
        
        corrections = [c['correction'] for c in self.calibration_data['corrections']]
        
        avg_correction = np.mean(corrections)
        std_correction = np.std(corrections)
        
        # High confidence if corrections are consistent
        confidence = 1.0 - min(std_correction / (abs(avg_correction) + 1), 1.0)
        
        # Suggest adjustment if average correction is significant
        if abs(avg_correction) > 0.2 and confidence > 0.5:
            return True, avg_correction, confidence
        
        return False, 0.0, confidence

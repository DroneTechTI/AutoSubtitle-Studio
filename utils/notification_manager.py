"""
Desktop notification manager for user alerts
"""
import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage desktop notifications across different platforms"""
    
    def __init__(self, app_name="Subtitle Generator"):
        self.app_name = app_name
        self.system = platform.system()
        self._check_notification_support()
    
    def _check_notification_support(self):
        """Check if notifications are supported on this platform"""
        self.supported = False
        
        try:
            if self.system == "Windows":
                # Try to import win10toast for Windows notifications
                try:
                    from win10toast import ToastNotifier
                    self.notifier = ToastNotifier()
                    self.supported = True
                    logger.info("Windows notifications supported (win10toast)")
                except ImportError:
                    # Fallback to plyer
                    try:
                        from plyer import notification
                        self.notification = notification
                        self.supported = True
                        logger.info("Windows notifications supported (plyer)")
                    except ImportError:
                        logger.warning("Desktop notifications not available. Install 'win10toast' or 'plyer' for notification support.")
                        
            elif self.system in ["Linux", "Darwin"]:  # Darwin = macOS
                # Try to use plyer for cross-platform notifications
                try:
                    from plyer import notification
                    self.notification = notification
                    self.supported = True
                    logger.info(f"{self.system} notifications supported (plyer)")
                except ImportError:
                    logger.warning("Desktop notifications not available. Install 'plyer' for notification support.")
            else:
                logger.warning(f"Desktop notifications not supported on {self.system}")
                
        except Exception as e:
            logger.error(f"Error checking notification support: {str(e)}")
    
    def show_notification(self, title, message, duration=10, icon_path=None):
        """
        Show a desktop notification
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds (default: 10)
            icon_path: Optional path to icon file
        
        Returns:
            True if notification was shown, False otherwise
        """
        if not self.supported:
            logger.debug("Notifications not supported, skipping")
            return False
        
        try:
            if self.system == "Windows":
                # Try win10toast first
                if hasattr(self, 'notifier'):
                    try:
                        self.notifier.show_toast(
                            title=title,
                            msg=message,
                            duration=duration,
                            icon_path=icon_path,
                            threaded=True  # Non-blocking
                        )
                        logger.info(f"Notification shown: {title}")
                        return True
                    except Exception as e:
                        logger.debug(f"win10toast failed: {str(e)}, trying fallback")
                
                # Fallback to plyer
                if hasattr(self, 'notification'):
                    self.notification.notify(
                        title=title,
                        message=message,
                        app_name=self.app_name,
                        timeout=duration
                    )
                    logger.info(f"Notification shown: {title}")
                    return True
                    
            else:
                # Linux/macOS using plyer
                if hasattr(self, 'notification'):
                    self.notification.notify(
                        title=title,
                        message=message,
                        app_name=self.app_name,
                        timeout=duration,
                        app_icon=icon_path
                    )
                    logger.info(f"Notification shown: {title}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error showing notification: {str(e)}")
            return False
    
    def show_success(self, message, title=None):
        """
        Show a success notification
        
        Args:
            message: Success message
            title: Optional custom title (default: "Operazione Completata")
        
        Returns:
            True if notification was shown
        """
        title = title or "✅ Operazione Completata"
        return self.show_notification(title, message, duration=10)
    
    def show_error(self, message, title=None):
        """
        Show an error notification
        
        Args:
            message: Error message
            title: Optional custom title (default: "Errore")
        
        Returns:
            True if notification was shown
        """
        title = title or "❌ Errore"
        return self.show_notification(title, message, duration=15)
    
    def show_warning(self, message, title=None):
        """
        Show a warning notification
        
        Args:
            message: Warning message
            title: Optional custom title (default: "Attenzione")
        
        Returns:
            True if notification was shown
        """
        title = title or "⚠️ Attenzione"
        return self.show_notification(title, message, duration=12)
    
    def show_info(self, message, title=None):
        """
        Show an info notification
        
        Args:
            message: Info message
            title: Optional custom title (default: "Informazione")
        
        Returns:
            True if notification was shown
        """
        title = title or "ℹ️ Informazione"
        return self.show_notification(title, message, duration=8)
    
    def is_supported(self):
        """
        Check if notifications are supported
        
        Returns:
            True if notifications are supported
        """
        return self.supported

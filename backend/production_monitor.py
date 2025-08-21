import logging
import json
from datetime import datetime

class ProductionMonitor:
    """Monitor enhanced CrewAI performance in production"""
    
    def __init__(self):
        self.session_data = []
    
    def log_session(self, screenshots, errors, success, duration):
        """Log discovery session metrics"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "screenshots": screenshots,
            "errors": errors,
            "success": success,
            "duration": duration
        }
        self.session_data.append(data)
        
        # Log to file
        with open("backend/fs_files/production_metrics.json", "a") as f:
            f.write(f"{json.dumps(data)}\n")
        
        logging.info(f"📊 Session logged: {screenshots} screenshots, {errors} errors, success: {success}")
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.session_data:
            return "No sessions recorded yet"
        
        total_sessions = len(self.session_data)
        successful_sessions = sum(1 for s in self.session_data if s['success'])
        avg_screenshots = sum(s['screenshots'] for s in self.session_data) / total_sessions
        
        return f"Performance: {successful_sessions}/{total_sessions} success rate, avg {avg_screenshots:.1f} screenshots"

production_monitor = ProductionMonitor()

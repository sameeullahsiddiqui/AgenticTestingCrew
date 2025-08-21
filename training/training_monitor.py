import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingMonitor:
    """Real-time monitoring system for CrewAI training pipeline"""
    
    def __init__(self, log_dir: str = "training/logs", update_interval: int = 5):
        self.log_dir = log_dir
        self.update_interval = update_interval
        self.monitoring = False
        self.metrics = {}
        self.training_start_time = None
        self.current_phase = None
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logging
        self.monitor_log = os.path.join(self.log_dir, f"training_monitor_{int(time.time())}.log")
        
        # Metrics tracking
        self.performance_history = []
        self.error_log = []
        self.phase_progress = {}
        
    def start_monitoring(self):
        """Start the monitoring system"""
        logger.info("🔍 Starting Training Monitor...")
        self.monitoring = True
        self.training_start_time = datetime.now()
        
        # Start monitoring threads
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        # Start metrics collection
        metrics_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        metrics_thread.start()
        
        logger.info("✅ Training Monitor started")
        
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring = False
        logger.info("🛑 Training Monitor stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Update dashboard
                self._update_dashboard()
                
                # Check for training files
                self._check_training_progress()
                
                # Monitor system resources
                self._monitor_system_resources()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
    def _collect_metrics(self):
        """Collect training metrics"""
        while self.monitoring:
            try:
                # Collect current metrics
                current_metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "training_time": self._get_training_duration(),
                    "current_phase": self.current_phase,
                    "system_memory": self._get_memory_usage(),
                    "disk_usage": self._get_disk_usage(),
                    "errors_count": len(self.error_log)
                }
                
                # Check for training files
                if os.path.exists("training/datasets"):
                    current_metrics["datasets_created"] = len([f for f in os.listdir("training/datasets") if f.endswith('.jsonl')])
                
                # Check for model files
                if os.path.exists("training/models"):
                    current_metrics["models_created"] = len([f for f in os.listdir("training/models") if f.endswith('.json') or f.endswith('.yaml')])
                
                self.performance_history.append(current_metrics)
                
                # Save metrics to file
                with open(os.path.join(self.log_dir, "metrics.json"), "w") as f:
                    json.dump(self.performance_history[-50:], f, indent=2)  # Keep last 50 entries
                
                time.sleep(10)  # Collect metrics every 10 seconds
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    def _update_dashboard(self):
        """Update the monitoring dashboard"""
        try:
            # Create dashboard content
            dashboard = self._generate_dashboard()
            
            # Save dashboard to file
            dashboard_file = os.path.join(self.log_dir, "dashboard.txt")
            with open(dashboard_file, "w", encoding='utf-8') as f:
                f.write(dashboard)
                
            # Print to console (clear screen first)
            if os.name == 'nt':  # Windows
                os.system('cls')
            else:  # Unix/Linux
                os.system('clear')
                
            print(dashboard)
            
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")
    
    def _generate_dashboard(self) -> str:
        """Generate monitoring dashboard content"""
        training_time = self._get_training_duration()
        
        dashboard = f"""
{'='*80}
🚀 CREWAI TRAINING PIPELINE MONITOR
{'='*80}

⏱️  TRAINING TIME: {training_time}
📍 CURRENT PHASE: {self.current_phase or 'Initializing...'}
🔄 STATUS: {'Running' if self.monitoring else 'Stopped'}

📊 SYSTEM METRICS:
   Memory Usage: {self._get_memory_usage():.1f}%
   Disk Usage: {self._get_disk_usage():.1f}%
   Errors: {len(self.error_log)}

📁 TRAINING PROGRESS:
   Datasets Created: {self._count_files('training/datasets', '.jsonl')}
   Models: {self._count_files('training/models', '.yaml')}
   Evaluation Results: {self._count_files('training/evaluation', '.json')}

📈 RECENT ACTIVITY:
{self._get_recent_activity()}

🎯 CURRENT OBJECTIVES:
   ✅ Data Generation Complete
   {'✅' if self.current_phase != 'data_generation' else '🔄'} Training In Progress  
   {'✅' if 'validation' in str(self.current_phase) else '⏳'} Validation Phase
   {'✅' if 'complete' in str(self.current_phase) else '⏳'} Training Complete

{'='*80}
📋 Last Updated: {datetime.now().strftime('%H:%M:%S')}
{'='*80}
"""
        
        return dashboard
    
    def _get_training_duration(self) -> str:
        """Get training duration as formatted string"""
        if not self.training_start_time:
            return "00:00:00"
            
        duration = datetime.now() - self.training_start_time
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _get_memory_usage(self) -> float:
        """Get system memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('.').percent
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def _count_files(self, directory: str, extension: str) -> int:
        """Count files with specific extension in directory"""
        if not os.path.exists(directory):
            return 0
        return len([f for f in os.listdir(directory) if f.endswith(extension)])
    
    def _get_recent_activity(self) -> str:
        """Get recent training activity"""
        activity_lines = []
        
        # Check for recent log files
        if os.path.exists(self.log_dir):
            log_files = [f for f in os.listdir(self.log_dir) if f.endswith('.log')]
            if log_files:
                latest_log = max([os.path.join(self.log_dir, f) for f in log_files], 
                               key=os.path.getmtime)
                try:
                    with open(latest_log, 'r') as f:
                        lines = f.readlines()[-5:]  # Last 5 lines
                        for line in lines:
                            if line.strip():
                                activity_lines.append(f"   {line.strip()}")
                except Exception:
                    pass
        
        if not activity_lines:
            activity_lines = [
                f"   {datetime.now().strftime('%H:%M:%S')} - Training monitor started",
                f"   {datetime.now().strftime('%H:%M:%S')} - Initializing training pipeline..."
            ]
        
        return '\n'.join(activity_lines[-3:])  # Show last 3 lines
    
    def _check_training_progress(self):
        """Check training progress from files"""
        # Check for training phase indicators
        phase_files = {
            'data_generation': 'training/datasets/train.jsonl',
            'baseline_evaluation': 'training/evaluation/baseline_metrics.json',
            'training_phase_1': 'training/models/training_progress.json',
            'validation': 'training/evaluation/validation_results.json',
            'complete': 'training/TRAINING_REPORT.md'
        }
        
        for phase, file_path in phase_files.items():
            if os.path.exists(file_path):
                if self.current_phase != phase:
                    self.current_phase = phase
                    logger.info(f"📍 Training phase updated: {phase}")
                    
    def _monitor_system_resources(self):
        """Monitor system resources and log warnings"""
        try:
            memory_usage = self._get_memory_usage()
            disk_usage = self._get_disk_usage()
            
            # Log warnings if resources are high
            if memory_usage > 85:
                warning = f"High memory usage: {memory_usage:.1f}%"
                logger.warning(warning)
                self.error_log.append({"timestamp": datetime.now().isoformat(), "type": "warning", "message": warning})
                
            if disk_usage > 90:
                warning = f"High disk usage: {disk_usage:.1f}%"
                logger.warning(warning)
                self.error_log.append({"timestamp": datetime.now().isoformat(), "type": "warning", "message": warning})
                
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
    
    def log_training_event(self, event: str, details: Dict[str, Any] = None):
        """Log a training event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details or {}
        }
        
        # Write to log file
        log_file = os.path.join(self.log_dir, "training_events.log")
        with open(log_file, "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")
        
        logger.info(f"📝 Training event: {event}")

class TrainingExecutor:
    """Execute training pipeline with monitoring"""
    
    def __init__(self, monitor: TrainingMonitor):
        self.monitor = monitor
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def run_training_pipeline(self):
        """Run the complete training pipeline with monitoring"""
        logger.info("🚀 Starting CrewAI Training Pipeline with Monitoring...")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        try:
            # Step 1: Generate Training Data
            logger.info("📊 Step 1: Generating Training Data...")
            self.monitor.log_training_event("data_generation_start")
            await self._run_step("python data_generator.py --scenarios 500", "Data Generation")
            
            # Step 2: Baseline Evaluation
            logger.info("📈 Step 2: Running Baseline Evaluation...")
            self.monitor.log_training_event("baseline_evaluation_start")
            await self._run_step("python evaluation/performance_metrics.py --model baseline", "Baseline Evaluation")
            
            # Step 3: Training Phases
            logger.info("🧠 Step 3: Running Training Phases...")
            self.monitor.log_training_event("training_start")
            await self._run_step("python training_pipeline.py --step train", "Training")
            
            # Step 4: Validation
            logger.info("✅ Step 4: Running Validation Tests...")
            self.monitor.log_training_event("validation_start")
            await self._run_step("python training_pipeline.py --step validate", "Validation")
            
            # Step 5: Generate Report
            logger.info("📋 Step 5: Generating Training Report...")
            self.monitor.log_training_event("report_generation_start")
            await self._run_step("python training_pipeline.py --step report", "Report Generation")
            
            logger.info("🎉 Training Pipeline Completed Successfully!")
            self.monitor.log_training_event("training_complete")
            
        except Exception as e:
            logger.error(f"❌ Training pipeline failed: {e}")
            self.monitor.log_training_event("training_failed", {"error": str(e)})
        
        finally:
            # Keep monitoring for a bit to show final results
            await asyncio.sleep(10)
            self.monitor.stop_monitoring()
    
    async def _run_step(self, command: str, step_name: str):
        """Run a training step with monitoring"""
        logger.info(f"🔄 Executing: {step_name}")
        
        # Change to training directory
        os.chdir("training")
        
        try:
            # Run command
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="."
            )
            
            # Monitor process output
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ {step_name} completed successfully")
                self.monitor.log_training_event(f"{step_name.lower().replace(' ', '_')}_complete")
            else:
                logger.error(f"❌ {step_name} failed: {stderr}")
                self.monitor.log_training_event(f"{step_name.lower().replace(' ', '_')}_failed", {"error": stderr})
                
        except Exception as e:
            logger.error(f"❌ Error executing {step_name}: {e}")
            self.monitor.log_training_event(f"{step_name.lower().replace(' ', '_')}_error", {"error": str(e)})
        
        finally:
            # Change back to root directory
            os.chdir("..")

async def main():
    """Main function to run training with monitoring"""
    # Create monitor
    monitor = TrainingMonitor()
    
    # Create executor
    executor = TrainingExecutor(monitor)
    
    # Run training pipeline
    await executor.run_training_pipeline()
    
    print("\n🎉 Training pipeline with monitoring completed!")
    print(f"📁 Check training/logs/ for detailed monitoring data")
    print(f"📊 Check training/TRAINING_REPORT.md for results")

if __name__ == "__main__":
    asyncio.run(main())

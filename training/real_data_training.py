#!/usr/bin/env python3
"""
Real Data Training Pipeline for CrewAI
Train the model using actual discovery session data from production runs
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RealTrainingExample:
    """Training example from real discovery session data"""
    session_id: str
    url: str
    input_prompt: str
    actual_response: str
    screenshots_taken: int
    errors_encountered: List[str]
    success: bool
    duration: float
    discovered_pages: List[str]
    tools_used: List[str]
    
class RealDataCollector:
    """Collect training data from actual CrewAI discovery sessions"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent / "backend"
        self.fs_files_dir = self.backend_dir / "fs_files"
        self.training_dir = Path(__file__).parent
        self.real_data_dir = self.training_dir / "real_data"
        self.real_data_dir.mkdir(exist_ok=True)
        
    def collect_session_data(self) -> List[RealTrainingExample]:
        """Collect training data from all discovery session runs"""
        logger.info("🔍 Collecting real data from discovery sessions...")
        
        training_examples = []
        
        if not self.fs_files_dir.exists():
            logger.warning("❌ No fs_files directory found - run some discovery sessions first")
            return training_examples
            
        # Scan all run directories
        run_dirs = [d for d in self.fs_files_dir.iterdir() if d.is_dir() and d.name.startswith('run_')]
        logger.info(f"📁 Found {len(run_dirs)} discovery session directories")
        
        for run_dir in run_dirs:
            try:
                example = self._process_session_directory(run_dir)
                if example:
                    training_examples.append(example)
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to process {run_dir.name}: {e}")
                continue
                
        logger.info(f"✅ Collected {len(training_examples)} real training examples")
        return training_examples
    
    def _process_session_directory(self, run_dir: Path) -> RealTrainingExample:
        """Process a single discovery session directory"""
        
        # Load discovery summary
        discovery_file = run_dir / "discovery_summary.json"
        site_map_file = run_dir / "site_map.json"
        
        session_data = {
            "session_id": run_dir.name,
            "screenshots_taken": 0,
            "errors_encountered": [],
            "success": False,
            "duration": 0.0,
            "discovered_pages": [],
            "tools_used": [],
            "url": "",
            "input_prompt": "",
            "actual_response": ""
        }
        
        # Count screenshots
        screenshots_dir = run_dir / "screenshots"
        if screenshots_dir.exists():
            screenshots = list(screenshots_dir.glob("*.png"))
            session_data["screenshots_taken"] = len(screenshots)
            
        # Load discovery results
        if discovery_file.exists():
            try:
                with open(discovery_file) as f:
                    discovery_data = json.load(f)
                    session_data["url"] = discovery_data.get("base_url", "")
                    session_data["discovered_pages"] = discovery_data.get("pages_discovered", [])
                    session_data["success"] = len(session_data["discovered_pages"]) >= 10
                    
            except Exception as e:
                logger.warning(f"Failed to load discovery data: {e}")
                
        # Load site map
        if site_map_file.exists():
            try:
                with open(site_map_file) as f:
                    site_data = json.load(f)
                    session_data["actual_response"] = json.dumps(site_data, indent=2)
                    
            except Exception as e:
                logger.warning(f"Failed to load site map: {e}")
                
        # Load logs for errors and tools
        logs_dir = run_dir / "logs"
        if logs_dir.exists():
            session_data.update(self._extract_log_data(logs_dir))
            
        # Load crew output log
        crew_log = run_dir / "crew_output.log.txt"
        if crew_log.exists():
            try:
                with open(crew_log) as f:
                    log_content = f.read()
                    session_data["input_prompt"] = self._extract_input_prompt(log_content)
                    session_data["tools_used"] = self._extract_tools_used(log_content)
                    session_data["duration"] = self._extract_duration(log_content)
                    
            except Exception as e:
                logger.warning(f"Failed to process crew log: {e}")
        
        return RealTrainingExample(
            session_id=session_data["session_id"],
            url=session_data["url"],
            input_prompt=session_data["input_prompt"],
            actual_response=session_data["actual_response"],
            screenshots_taken=session_data["screenshots_taken"],
            errors_encountered=session_data["errors_encountered"],
            success=session_data["success"],
            duration=session_data["duration"],
            discovered_pages=session_data["discovered_pages"],
            tools_used=session_data["tools_used"]
        )
    
    def _extract_log_data(self, logs_dir: Path) -> Dict[str, Any]:
        """Extract error and tool usage data from logs"""
        
        data = {
            "errors_encountered": [],
            "tools_used": []
        }
        
        for log_file in logs_dir.glob("*.log"):
            try:
                with open(log_file) as f:
                    content = f.read()
                    
                    # Extract errors
                    if "error" in content.lower() or "exception" in content.lower():
                        errors = self._parse_errors(content)
                        data["errors_encountered"].extend(errors)
                        
                    # Extract tool usage
                    tools = self._parse_tool_usage(content)
                    data["tools_used"].extend(tools)
                    
            except Exception as e:
                logger.warning(f"Failed to process log {log_file.name}: {e}")
                
        return data
    
    def _extract_input_prompt(self, log_content: str) -> str:
        """Extract the original input prompt from crew log"""
        
        # Look for common prompt patterns
        prompt_markers = [
            "Discover and map the application at",
            "Navigate through the application",
            "Explore the website"
        ]
        
        for marker in prompt_markers:
            if marker in log_content:
                # Extract the prompt section
                start_idx = log_content.find(marker)
                if start_idx != -1:
                    # Get the next 200 characters as the prompt
                    return log_content[start_idx:start_idx+200].strip()
                    
        return "Discover and map the application functionality"
    
    def _extract_tools_used(self, log_content: str) -> List[str]:
        """Extract tool usage patterns from log content"""
        
        tools = set()
        tool_patterns = [
            "browser_navigate", "browser_screenshot", "browser_click",
            "browser_wait_for", "browser_evaluate", "file_write"
        ]
        
        for tool in tool_patterns:
            if tool in log_content:
                tools.add(tool)
                
        return list(tools)
    
    def _extract_duration(self, log_content: str) -> float:
        """Extract session duration from log content"""
        
        # Look for timestamp patterns to calculate duration
        import re
        timestamps = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_content)
        
        if len(timestamps) >= 2:
            try:
                from datetime import datetime
                start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
                duration = (end_time - start_time).total_seconds()
                return duration
            except Exception:
                pass
                
        return 300.0  # Default 5 minutes
    
    def _parse_errors(self, content: str) -> List[str]:
        """Parse error messages from log content"""
        
        errors = []
        error_keywords = ["rate limit", "timeout", "connection", "failed", "error", "exception"]
        
        lines = content.split('\n')
        for line in lines:
            for keyword in error_keywords:
                if keyword in line.lower():
                    errors.append(line.strip()[:100])  # Limit error length
                    break
                    
        return list(set(errors))  # Remove duplicates
    
    def _parse_tool_usage(self, content: str) -> List[str]:
        """Parse tool usage from log content"""
        
        tools = []
        tool_patterns = [
            "Using tool", "Tool:", "browser_", "file_", "directory_"
        ]
        
        lines = content.split('\n')
        for line in lines:
            for pattern in tool_patterns:
                if pattern in line:
                    # Extract tool name
                    words = line.split()
                    for word in words:
                        if 'browser_' in word or 'file_' in word:
                            tools.append(word.replace(':', '').replace('(', ''))
                            
        return list(set(tools))
    
    def save_real_training_data(self, examples: List[RealTrainingExample]):
        """Save collected real data for training"""
        
        logger.info(f"💾 Saving {len(examples)} real training examples...")
        
        # Convert to JSON format
        training_data = []
        for example in examples:
            training_data.append({
                "session_id": example.session_id,
                "url": example.url,
                "input": example.input_prompt,
                "expected_output": example.actual_response,
                "metadata": {
                    "screenshots_taken": example.screenshots_taken,
                    "errors_encountered": example.errors_encountered,
                    "success": example.success,
                    "duration": example.duration,
                    "discovered_pages": example.discovered_pages,
                    "tools_used": example.tools_used,
                    "performance_score": self._calculate_performance_score(example)
                }
            })
        
        # Save to file
        output_file = self.real_data_dir / f"real_training_data_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2)
            
        logger.info(f"✅ Real training data saved to: {output_file}")
        
        # Generate summary
        self._generate_data_summary(training_data, output_file.parent / "real_data_summary.md")
        
        return output_file
    
    def _calculate_performance_score(self, example: RealTrainingExample) -> float:
        """Calculate performance score for training example"""
        
        score = 0.0
        
        # Screenshot score (0-40 points)
        if example.screenshots_taken >= 34:
            score += 40
        elif example.screenshots_taken >= 20:
            score += 30
        elif example.screenshots_taken >= 10:
            score += 20
        else:
            score += 10
            
        # Success score (0-30 points)
        if example.success:
            score += 30
        elif len(example.discovered_pages) > 5:
            score += 20
        else:
            score += 10
            
        # Error recovery score (0-20 points)
        if len(example.errors_encountered) == 0:
            score += 20
        elif len(example.errors_encountered) <= 2:
            score += 15
        else:
            score += 5
            
        # Tool usage score (0-10 points)
        if len(example.tools_used) >= 5:
            score += 10
        elif len(example.tools_used) >= 3:
            score += 7
        else:
            score += 3
            
        return score / 100.0  # Normalize to 0-1
    
    def _generate_data_summary(self, training_data: List[Dict], output_file: Path):
        """Generate summary of collected real data"""
        
        total_examples = len(training_data)
        successful_sessions = sum(1 for ex in training_data if ex["metadata"]["success"])
        avg_screenshots = sum(ex["metadata"]["screenshots_taken"] for ex in training_data) / total_examples if total_examples > 0 else 0
        avg_performance = sum(ex["metadata"]["performance_score"] for ex in training_data) / total_examples if total_examples > 0 else 0
        
        # Count unique URLs
        unique_urls = set(ex["url"] for ex in training_data if ex["url"])
        
        # Count error types
        all_errors = []
        for ex in training_data:
            all_errors.extend(ex["metadata"]["errors_encountered"])
            
        summary = f'''# Real Data Collection Summary

## Collection Results
- **Total Examples**: {total_examples}
- **Successful Sessions**: {successful_sessions} ({successful_sessions/total_examples*100:.1f}%)
- **Average Screenshots**: {avg_screenshots:.1f}
- **Average Performance Score**: {avg_performance:.3f}
- **Unique URLs Tested**: {len(unique_urls)}

## Data Quality Assessment
- **High Quality Examples** (score ≥ 0.8): {sum(1 for ex in training_data if ex["metadata"]["performance_score"] >= 0.8)}
- **Medium Quality Examples** (score 0.6-0.8): {sum(1 for ex in training_data if 0.6 <= ex["metadata"]["performance_score"] < 0.8)}
- **Low Quality Examples** (score < 0.6): {sum(1 for ex in training_data if ex["metadata"]["performance_score"] < 0.6)}

## Common Errors Encountered
- **Total Error Instances**: {len(all_errors)}
- **Unique Error Types**: {len(set(all_errors))}

## URLs Tested
{chr(10).join(f"- {url}" for url in sorted(unique_urls))}

## Training Recommendations
- Use high-quality examples for fine-tuning core behaviors
- Use medium-quality examples for error recovery training
- Analyze low-quality examples for improvement opportunities

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
        
        with open(output_file, 'w') as f:
            f.write(summary)
            
        logger.info(f"📊 Data summary saved to: {output_file}")

class RealDataTrainingPipeline:
    """Training pipeline using real session data"""
    
    def __init__(self):
        self.collector = RealDataCollector()
        self.training_dir = Path(__file__).parent
        
    def run_real_data_training(self):
        """Execute training with real data"""
        
        logger.info("🚀 Starting Real Data Training Pipeline...")
        
        # Step 1: Collect real data
        real_examples = self.collector.collect_session_data()
        
        if not real_examples:
            logger.error("❌ No real training data found!")
            logger.info("💡 To collect real data:")
            logger.info("   1. Run discovery sessions through crew_orchestrator.py")
            logger.info("   2. Let sessions complete and generate results")
            logger.info("   3. Re-run this training script")
            return False
            
        # Step 2: Save real data
        data_file = self.collector.save_real_training_data(real_examples)
        
        # Step 3: Analyze data quality
        high_quality = [ex for ex in real_examples if self.collector._calculate_performance_score(ex) >= 0.8]
        medium_quality = [ex for ex in real_examples if 0.6 <= self.collector._calculate_performance_score(ex) < 0.8]
        low_quality = [ex for ex in real_examples if self.collector._calculate_performance_score(ex) < 0.6]
        
        logger.info(f"📊 Data Quality Analysis:")
        logger.info(f"   High Quality: {len(high_quality)} examples")
        logger.info(f"   Medium Quality: {len(medium_quality)} examples")
        logger.info(f"   Low Quality: {len(low_quality)} examples")
        
        # Step 4: Generate enhanced training data
        if high_quality:
            self._create_enhanced_training_dataset(high_quality, medium_quality)
            
        # Step 5: Update training configuration
        self._update_training_config(real_examples)
        
        logger.info("🎉 Real data training preparation complete!")
        logger.info("✅ Next step: Run enhanced training with real data")
        
        return True
    
    def _create_enhanced_training_dataset(self, high_quality: List, medium_quality: List):
        """Create enhanced training dataset from real data"""
        
        logger.info("🔧 Creating enhanced training dataset from real data...")
        
        enhanced_dataset = []
        
        # Process high-quality examples for success patterns
        for example in high_quality:
            enhanced_dataset.append({
                "type": "success_pattern",
                "input": f"Discover application at {example.url}",
                "expected_behavior": f"Take {example.screenshots_taken}+ screenshots, discover {len(example.discovered_pages)}+ pages",
                "tools": example.tools_used,
                "performance_target": "high_completion_rate"
            })
            
        # Process medium-quality examples for improvement
        for example in medium_quality:
            enhanced_dataset.append({
                "type": "improvement_pattern", 
                "input": f"Discover application at {example.url}",
                "expected_behavior": f"Improve from {example.screenshots_taken} to 34+ screenshots",
                "errors_to_avoid": example.errors_encountered,
                "performance_target": "error_recovery"
            })
            
        # Save enhanced dataset
        output_file = self.training_dir / "real_data" / "enhanced_training_dataset.json"
        with open(output_file, 'w') as f:
            json.dump(enhanced_dataset, f, indent=2)
            
        logger.info(f"✅ Enhanced dataset created: {output_file}")
        logger.info(f"   Success patterns: {len([ex for ex in enhanced_dataset if ex['type'] == 'success_pattern'])}")
        logger.info(f"   Improvement patterns: {len([ex for ex in enhanced_dataset if ex['type'] == 'improvement_pattern'])}")
        
    def _update_training_config(self, examples: List[RealTrainingExample]):
        """Update training configuration with real data insights"""
        
        # Calculate real performance metrics
        avg_screenshots = sum(ex.screenshots_taken for ex in examples) / len(examples)
        success_rate = sum(1 for ex in examples if ex.success) / len(examples)
        avg_errors = sum(len(ex.errors_encountered) for ex in examples) / len(examples)
        
        config = {
            "real_data_training": {
                "enabled": True,
                "data_source": "production_sessions",
                "examples_count": len(examples),
                "baseline_metrics": {
                    "avg_screenshots": round(avg_screenshots, 1),
                    "success_rate": round(success_rate, 3),
                    "avg_errors": round(avg_errors, 1)
                },
                "improvement_targets": {
                    "target_screenshots": max(34, int(avg_screenshots * 1.5)),
                    "target_success_rate": min(0.95, success_rate * 1.5),
                    "target_error_reduction": max(0.1, avg_errors * 0.5)
                },
                "training_focus": [
                    "screenshot_consistency",
                    "error_recovery", 
                    "session_completion"
                ]
            }
        }
        
        config_file = self.training_dir / "models" / "real_data_config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"✅ Training config updated: {config_file}")

def main():
    """Main function to run real data training"""
    
    print("🎯 CrewAI Real Data Training Pipeline")
    print("Collect and use actual discovery session data for training")
    print("=" * 60)
    
    pipeline = RealDataTrainingPipeline()
    success = pipeline.run_real_data_training()
    
    if success:
        print("\n🎉 Real data collection and training preparation complete!")
        print("\n📋 What was accomplished:")
        print("✅ Collected training data from actual discovery sessions")
        print("✅ Analyzed data quality and performance patterns")
        print("✅ Created enhanced training dataset from real examples")
        print("✅ Updated training configuration with real metrics")
        
        print("\n🚀 Next steps:")
        print("1. Review the collected data in training/real_data/")
        print("2. Run enhanced training: python training_pipeline.py --real-data")
        print("3. Compare performance before/after real data training")
        
    else:
        print("\n❌ No real data found for training")
        print("\n💡 To generate real training data:")
        print("1. Run several discovery sessions:")
        print("   python backend/crew_orchestrator.py")
        print("2. Try different URLs and scenarios")
        print("3. Let sessions complete fully")
        print("4. Re-run this script to collect the data")

if __name__ == "__main__":
    main()

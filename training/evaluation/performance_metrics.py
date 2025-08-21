import json
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass 
class EvaluationResult:
    """Results from a single evaluation run"""
    test_name: str
    success: bool
    score: float
    metrics: Dict[str, Any]
    execution_time: float
    errors: List[str]

class CrewAIEvaluator:
    """Comprehensive evaluation suite for CrewAI performance"""
    
    def __init__(self, crew_instance=None, baseline_data: Optional[str] = None):
        self.crew = crew_instance
        self.baseline_data = baseline_data
        self.results = []
        
        # Load baseline performance if available
        if baseline_data and os.path.exists(baseline_data):
            with open(baseline_data, 'r') as f:
                self.baseline = json.load(f)
        else:
            self.baseline = {}
    
    def evaluate_tool_accuracy(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate accuracy of tool selection and usage"""
        start_time = time.time()
        errors = []
        correct_tools = 0
        total_tools = 0
        
        for case in test_cases:
            expected_tools = case['expected_tools']
            input_prompt = case['input_prompt']
            
            try:
                # Run crew with test input (simplified)
                result = self._run_crew_test(input_prompt)
                predicted_tools = self._extract_tools_from_result(result)
                
                # Compare predicted vs expected tools
                matches = len(set(predicted_tools) & set(expected_tools))
                total = len(expected_tools)
                
                correct_tools += matches
                total_tools += total
                
            except Exception as e:
                errors.append(f"Tool accuracy test failed: {str(e)}")
        
        score = correct_tools / max(total_tools, 1)
        execution_time = time.time() - start_time
        
        return EvaluationResult(
            test_name="tool_accuracy",
            success=len(errors) == 0,
            score=score,
            metrics={
                "correct_tools": correct_tools,
                "total_tools": total_tools,
                "accuracy_percentage": score * 100
            },
            execution_time=execution_time,
            errors=errors
        )
    
    def evaluate_task_completion(self, test_scenarios: List[Dict]) -> EvaluationResult:
        """Evaluate ability to complete full tasks without early termination"""
        start_time = time.time()
        errors = []
        completed_tasks = 0
        
        for scenario in test_scenarios:
            target_screenshots = scenario.get('target_screenshots', 34)
            max_duration = scenario.get('max_duration_minutes', 30)
            
            try:
                result = self._run_crew_test(scenario['input_prompt'], max_duration * 60)
                
                # Check completion criteria
                screenshot_count = self._count_screenshots_in_result(result)
                task_complete = screenshot_count >= target_screenshots
                
                if task_complete:
                    completed_tasks += 1
                else:
                    errors.append(f"Task incomplete: {screenshot_count}/{target_screenshots} screenshots")
                    
            except Exception as e:
                errors.append(f"Task completion test failed: {str(e)}")
        
        score = completed_tasks / max(len(test_scenarios), 1)
        execution_time = time.time() - start_time
        
        return EvaluationResult(
            test_name="task_completion",
            success=len(errors) == 0,
            score=score,
            metrics={
                "completed_tasks": completed_tasks,
                "total_scenarios": len(test_scenarios),
                "completion_rate": score * 100
            },
            execution_time=execution_time,
            errors=errors
        )
    
    def evaluate_response_efficiency(self, test_inputs: List[str]) -> EvaluationResult:
        """Evaluate efficiency of agent responses (token usage, response length)"""
        start_time = time.time()
        errors = []
        total_efficiency = 0
        
        for test_input in test_inputs:
            try:
                result = self._run_crew_test(test_input)
                
                # Calculate efficiency metrics
                response_length = len(result.get('response', '').split())
                tool_count = len(self._extract_tools_from_result(result))
                
                # Efficiency = tools executed per response token (higher is better)
                efficiency = tool_count / max(response_length, 1)
                total_efficiency += efficiency
                
            except Exception as e:
                errors.append(f"Efficiency test failed: {str(e)}")
        
        average_efficiency = total_efficiency / max(len(test_inputs), 1)
        execution_time = time.time() - start_time
        
        return EvaluationResult(
            test_name="response_efficiency",
            success=len(errors) == 0,
            score=min(average_efficiency * 10, 1.0),  # Normalized score
            metrics={
                "average_efficiency": average_efficiency,
                "total_tests": len(test_inputs),
                "token_efficiency": average_efficiency
            },
            execution_time=execution_time,
            errors=errors
        )
    
    def evaluate_error_recovery(self, error_scenarios: List[Dict]) -> EvaluationResult:
        """Evaluate ability to recover from errors and continue tasks"""
        start_time = time.time()
        errors = []
        successful_recoveries = 0
        
        for scenario in error_scenarios:
            error_type = scenario['error_type']
            test_input = scenario['input_prompt']
            expected_recovery = scenario['expected_recovery']
            
            try:
                # Simulate error condition
                result = self._run_crew_test_with_simulated_error(test_input, error_type)
                
                # Check if recovery occurred
                recovery_successful = self._check_error_recovery(result, expected_recovery)
                
                if recovery_successful:
                    successful_recoveries += 1
                else:
                    errors.append(f"Failed to recover from {error_type}")
                    
            except Exception as e:
                errors.append(f"Error recovery test failed: {str(e)}")
        
        score = successful_recoveries / max(len(error_scenarios), 1)
        execution_time = time.time() - start_time
        
        return EvaluationResult(
            test_name="error_recovery",
            success=len(errors) == 0,
            score=score,
            metrics={
                "successful_recoveries": successful_recoveries,
                "total_scenarios": len(error_scenarios),
                "recovery_rate": score * 100
            },
            execution_time=execution_time,
            errors=errors
        )
    
    def run_benchmark_suite(self, benchmark_config: Dict) -> Dict[str, EvaluationResult]:
        """Run comprehensive benchmark evaluation"""
        logger.info("🚀 Starting CrewAI Benchmark Evaluation...")
        
        results = {}
        
        # Load test data
        test_data = self._load_test_data(benchmark_config.get('test_data_path', 'training/datasets/test.jsonl'))
        
        # 1. Tool Accuracy Test
        logger.info("📋 Running tool accuracy tests...")
        tool_test_cases = [
            {
                'input_prompt': item['input_prompt'],
                'expected_tools': item['tools_used']
            }
            for item in test_data[:20]  # Use first 20 examples
        ]
        results['tool_accuracy'] = self.evaluate_tool_accuracy(tool_test_cases)
        
        # 2. Task Completion Test
        logger.info("🎯 Running task completion tests...")
        completion_scenarios = [
            {
                'input_prompt': item['input_prompt'],
                'target_screenshots': item['success_criteria'].get('min_screenshots', 34),
                'max_duration_minutes': 15
            }
            for item in test_data[:10]  # Use first 10 examples
        ]
        results['task_completion'] = self.evaluate_task_completion(completion_scenarios)
        
        # 3. Response Efficiency Test  
        logger.info("⚡ Running response efficiency tests...")
        efficiency_inputs = [item['input_prompt'] for item in test_data[:15]]
        results['response_efficiency'] = self.evaluate_response_efficiency(efficiency_inputs)
        
        # 4. Error Recovery Test
        logger.info("🔧 Running error recovery tests...")
        error_scenarios = [
            {
                'error_type': 'rate_limit',
                'input_prompt': 'Discover 34+ pages with rate limiting',
                'expected_recovery': 'retry_with_delay'
            },
            {
                'error_type': 'element_not_found',
                'input_prompt': 'Click on non-existent menu item',
                'expected_recovery': 'alternative_selector'
            },
            {
                'error_type': 'timeout',
                'input_prompt': 'Navigate to slow-loading page',
                'expected_recovery': 'extend_wait_time'
            }
        ]
        results['error_recovery'] = self.evaluate_error_recovery(error_scenarios)
        
        # Generate summary
        self._generate_benchmark_report(results)
        
        return results
    
    def compare_with_baseline(self, current_results: Dict[str, EvaluationResult]) -> Dict[str, float]:
        """Compare current results with baseline performance"""
        improvements = {}
        
        for test_name, result in current_results.items():
            baseline_score = self.baseline.get(test_name, {}).get('score', 0.0)
            current_score = result.score
            improvement = ((current_score - baseline_score) / max(baseline_score, 0.001)) * 100
            improvements[test_name] = improvement
            
        return improvements
    
    def save_results(self, results: Dict[str, EvaluationResult], output_path: str):
        """Save evaluation results to file"""
        serializable_results = {}
        
        for test_name, result in results.items():
            serializable_results[test_name] = {
                'success': result.success,
                'score': result.score,
                'metrics': result.metrics,
                'execution_time': result.execution_time,
                'errors': result.errors,
                'timestamp': datetime.now().isoformat()
            }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_path}")
    
    def _load_test_data(self, filepath: str) -> List[Dict]:
        """Load test data from JSONL file"""
        data = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
        return data
    
    def _run_crew_test(self, input_prompt: str, timeout: int = 300) -> Dict:
        """Run a single crew test (mock implementation)"""
        # This would integrate with actual CrewAI execution
        # For now, return mock results
        return {
            'response': 'browser_navigate → ✓\nbrowser_click → ✓\nbrowser_take_screenshot → Done',
            'tools_executed': ['browser_navigate', 'browser_click', 'browser_take_screenshot'],
            'screenshots_taken': 12,
            'completion_status': 'partial'
        }
    
    def _run_crew_test_with_simulated_error(self, input_prompt: str, error_type: str) -> Dict:
        """Run crew test with simulated error conditions"""
        # Mock error simulation
        return {
            'response': f'Error {error_type} encountered → Recovery initiated → ✓',
            'error_occurred': True,
            'recovery_attempted': True,
            'recovery_successful': True
        }
    
    def _extract_tools_from_result(self, result: Dict) -> List[str]:
        """Extract tool names from execution result"""
        return result.get('tools_executed', [])
    
    def _count_screenshots_in_result(self, result: Dict) -> int:
        """Count screenshots taken in execution result"""
        return result.get('screenshots_taken', 0)
    
    def _check_error_recovery(self, result: Dict, expected_recovery: str) -> bool:
        """Check if error recovery was successful"""
        return result.get('recovery_successful', False)
    
    def _generate_benchmark_report(self, results: Dict[str, EvaluationResult]):
        """Generate and print benchmark report"""
        print("\n" + "="*80)
        print("🎯 CREWAI BENCHMARK EVALUATION REPORT")
        print("="*80)
        
        total_score = 0
        total_tests = 0
        
        for test_name, result in results.items():
            print(f"\n📊 {test_name.upper().replace('_', ' ')}")
            print(f"   Success: {'✅' if result.success else '❌'}")
            print(f"   Score: {result.score:.3f}")
            print(f"   Time: {result.execution_time:.2f}s")
            
            if result.errors:
                print(f"   Errors: {len(result.errors)}")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"     - {error}")
            
            total_score += result.score
            total_tests += 1
        
        average_score = total_score / max(total_tests, 1)
        print(f"\n🏆 OVERALL PERFORMANCE: {average_score:.3f}")
        
        if average_score >= 0.9:
            print("🎉 EXCELLENT - Ready for production!")
        elif average_score >= 0.7:
            print("👍 GOOD - Minor improvements needed")
        elif average_score >= 0.5:
            print("⚠️  FAIR - Significant training required")
        else:
            print("❌ POOR - Major improvements needed")
        
        print("="*80)

def main():
    """Main evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate CrewAI performance")
    parser.add_argument("--model", default="baseline", 
                       help="Model to evaluate (baseline, custom, fine_tuned)")
    parser.add_argument("--benchmark", default="full",
                       help="Benchmark suite to run (full, quick, specific)")
    parser.add_argument("--output", default="training/evaluation/results.json",
                       help="Output file for results")
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = CrewAIEvaluator()
    
    # Run benchmark
    benchmark_config = {
        'test_data_path': 'training/datasets/test.jsonl',
        'model_type': args.model,
        'benchmark_type': args.benchmark
    }
    
    results = evaluator.run_benchmark_suite(benchmark_config)
    
    # Save results
    evaluator.save_results(results, args.output)
    
    print(f"\n✅ Evaluation completed! Results saved to {args.output}")

if __name__ == "__main__":
    main()

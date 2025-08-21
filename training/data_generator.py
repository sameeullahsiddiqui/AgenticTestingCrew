import json
import os
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class TrainingExample:
    """Single training example for CrewAI fine-tuning"""
    input_prompt: str
    expected_output: str
    tools_used: List[str]
    success_criteria: Dict[str, Any]
    metadata: Dict[str, Any]

class CrewAIDataGenerator:
    """Generate synthetic training data for CrewAI agent improvement"""
    
    def __init__(self):
        self.web_elements = [
            "Administration", "Master Data Setup", "Projects", "Dashboard", 
            "Settings", "Reports", "Users", "Analytics", "Configuration",
            "Manage Users", "Clear Cache", "User Access Report", "Workflow History",
            "Business Units", "Departments", "Chart of Accounts", "Entity List",
            "Scoping", "Workplans", "Content Creation", "Data Collection",
            "Report Generation", "File Vault", "User Role Action Report"
        ]
        
        self.browser_tools = [
            "browser_navigate", "browser_click", "browser_take_screenshot",
            "browser_wait_for", "browser_type", "browser_hover", "browser_snapshot"
        ]
        
        self.response_patterns = [
            "✓", "Done", "Next", "Screenshot taken", "Progress saved",
            "Navigation complete", "Click executed", "Page loaded"
        ]

    def generate_discovery_examples(self, count: int = 100) -> List[TrainingExample]:
        """Generate browser discovery training examples"""
        examples = []
        
        for i in range(count):
            # Generate a realistic discovery scenario
            target_pages = random.randint(10, 50)
            menu_items = random.sample(self.web_elements[:9], random.randint(3, 6))
            
            # Create input prompt
            input_prompt = f"""
            Discover all pages in web application. Target: {target_pages}+ pages.
            Known menu items: {', '.join(menu_items)}
            
            Execute complete browser sequence:
            1. Navigate to base URL
            2. Click each menu item
            3. Take screenshots of all subpages
            4. Save progress regularly
            
            CRITICAL: Do not stop until {target_pages}+ screenshots taken.
            """
            
            # Generate expected tool sequence
            tool_sequence = []
            screenshot_count = 0
            
            for menu in menu_items:
                tool_sequence.extend([
                    f"browser_navigate: base_url",
                    f"browser_click: {menu}",
                    f"browser_take_screenshot: p{screenshot_count + 1}.png"
                ])
                screenshot_count += 1
                
                # Add submenu exploration
                submenus = random.sample(self.web_elements[9:], random.randint(2, 4))
                for submenu in submenus:
                    tool_sequence.extend([
                        f"browser_click: {submenu}",
                        f"browser_take_screenshot: p{screenshot_count + 1}.png"
                    ])
                    screenshot_count += 1
                    
                    if screenshot_count % 5 == 0:
                        tool_sequence.append("File Writer Tool: discovery_summary.json")
            
            # Expected output with minimal responses
            expected_output = "\n".join([
                f"{tool} → {random.choice(self.response_patterns)}" 
                for tool in tool_sequence
            ])
            
            example = TrainingExample(
                input_prompt=input_prompt.strip(),
                expected_output=expected_output,
                tools_used=list(set([t.split(':')[0] for t in tool_sequence])),
                success_criteria={
                    "min_screenshots": target_pages,
                    "must_save_progress": True,
                    "complete_all_menus": True,
                    "no_early_termination": True
                },
                metadata={
                    "scenario": "web_discovery",
                    "difficulty": "medium" if target_pages < 30 else "hard",
                    "generated_at": datetime.now().isoformat(),
                    "example_id": str(uuid.uuid4())
                }
            )
            
            examples.append(example)
        
        return examples

    def generate_error_recovery_examples(self, count: int = 50) -> List[TrainingExample]:
        """Generate examples for handling errors and rate limits"""
        examples = []
        error_scenarios = [
            "Rate limit exceeded - wait and retry",
            "Element not found - try alternative selector", 
            "Page load timeout - extend wait time",
            "Browser crashed - restart and resume",
            "Network error - retry with backoff"
        ]
        
        for i in range(count):
            scenario = random.choice(error_scenarios)
            
            if "rate limit" in scenario.lower():
                input_prompt = """
                Encountered Azure OpenAI rate limit during discovery.
                Current progress: 15/34 screenshots taken.
                Error: 429 Too Many Requests
                
                Action required: Implement rate limiting and continue.
                """
                
                expected_output = """
                Rate limit detected → ✓
                Implementing 5-second delay → ✓
                Resuming from screenshot p16 → ✓
                Continuing discovery sequence → ✓
                """
                
            elif "element not found" in scenario.lower():
                input_prompt = """
                Cannot find menu item "Administration" on page.
                Current action: browser_click: Administration
                Error: Element not located
                
                Try alternative approaches to find the element.
                """
                
                expected_output = """
                Element not found → ✓
                Trying snapshot for element discovery → ✓
                Alternative selector found → ✓
                Click executed successfully → ✓
                """
            
            else:
                continue
                
            example = TrainingExample(
                input_prompt=input_prompt.strip(),
                expected_output=expected_output.strip(),
                tools_used=["error_recovery", "browser_wait_for", "browser_snapshot"],
                success_criteria={
                    "handles_error_gracefully": True,
                    "continues_task": True,
                    "implements_retry_logic": True
                },
                metadata={
                    "scenario": "error_recovery",
                    "error_type": scenario,
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            examples.append(example)
        
        return examples

    def generate_optimization_examples(self, count: int = 30) -> List[TrainingExample]:
        """Generate examples for optimized agent behavior"""
        examples = []
        
        optimization_patterns = [
            "minimal_responses",
            "efficient_navigation",
            "batch_operations",
            "progress_tracking"
        ]
        
        for pattern in optimization_patterns:
            for i in range(count // len(optimization_patterns)):
                if pattern == "minimal_responses":
                    input_prompt = """
                    Execute browser discovery with minimal LLM usage.
                    Reduce verbose output to save tokens and avoid rate limits.
                    Focus on tool execution with brief confirmations only.
                    """
                    
                    expected_output = """
                    browser_navigate → ✓
                    browser_click → ✓  
                    browser_take_screenshot → Done
                    File Writer Tool → Saved
                    """
                    
                elif pattern == "efficient_navigation":
                    input_prompt = """
                    Optimize navigation sequence to minimize page loads.
                    Explore all submenus under each parent before moving.
                    Avoid unnecessary back-navigation when possible.
                    """
                    
                    expected_output = """
                    Exploring Administration submenu fully → ✓
                    All 6 Admin pages captured → ✓
                    Moving to next parent menu → ✓
                    Navigation optimized → ✓
                    """
                
                else:
                    continue
                    
                example = TrainingExample(
                    input_prompt=input_prompt.strip(),
                    expected_output=expected_output.strip(),
                    tools_used=["browser_navigate", "browser_click", "browser_take_screenshot"],
                    success_criteria={
                        "optimized_execution": True,
                        "minimal_token_usage": True,
                        "efficient_pattern": pattern
                    },
                    metadata={
                        "scenario": "optimization",
                        "pattern": pattern,
                        "generated_at": datetime.now().isoformat()
                    }
                )
                
                examples.append(example)
        
        return examples

    def save_training_data(self, examples: List[TrainingExample], filepath: str):
        """Save training examples to JSONL format"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for example in examples:
                json.dump(asdict(example), f, ensure_ascii=False)
                f.write('\n')
        
        print(f"Saved {len(examples)} training examples to {filepath}")

    def generate_full_dataset(self, output_dir: str = "training/datasets"):
        """Generate complete training dataset"""
        print("🚀 Generating CrewAI Training Dataset...")
        
        # Generate different types of examples
        discovery_examples = self.generate_discovery_examples(200)
        error_examples = self.generate_error_recovery_examples(100)
        optimization_examples = self.generate_optimization_examples(50)
        
        # Save individual datasets
        self.save_training_data(
            discovery_examples, 
            f"{output_dir}/discovery_training.jsonl"
        )
        
        self.save_training_data(
            error_examples,
            f"{output_dir}/error_recovery_training.jsonl" 
        )
        
        self.save_training_data(
            optimization_examples,
            f"{output_dir}/optimization_training.jsonl"
        )
        
        # Combine all examples
        all_examples = discovery_examples + error_examples + optimization_examples
        random.shuffle(all_examples)
        
        # Split into train/validation/test
        train_split = int(0.8 * len(all_examples))
        val_split = int(0.9 * len(all_examples))
        
        train_data = all_examples[:train_split]
        val_data = all_examples[train_split:val_split]
        test_data = all_examples[val_split:]
        
        self.save_training_data(train_data, f"{output_dir}/train.jsonl")
        self.save_training_data(val_data, f"{output_dir}/validation.jsonl")
        self.save_training_data(test_data, f"{output_dir}/test.jsonl")
        
        print(f"✅ Dataset Generated:")
        print(f"   - Training examples: {len(train_data)}")
        print(f"   - Validation examples: {len(val_data)}")
        print(f"   - Test examples: {len(test_data)}")
        print(f"   - Total examples: {len(all_examples)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CrewAI training data")
    parser.add_argument("--scenarios", type=int, default=350, 
                       help="Total number of scenarios to generate")
    parser.add_argument("--output", default="training/datasets",
                       help="Output directory for training data")
    
    args = parser.parse_args()
    
    generator = CrewAIDataGenerator()
    generator.generate_full_dataset(args.output)

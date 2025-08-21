"""
Dynamic Prompt Builder for Centralized Prompt Management

This module provides a flexible system for composing agent prompts and task descriptions
from reusable components, eliminating duplication and improving maintainability.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

class PromptBuilder:
    """
    Dynamic prompt composition engine that builds prompts from reusable components.
    
    Usage:
        prompt = PromptBuilder()
            .add_core("blazor_patterns", "navigation_expansion_strategy")
            .add_core("safety_rules", "exploration_safety_rules")
            .add_agent("discovery_agent", "main_instructions")
            .build({"BASE_URL": "https://example.com", "TARGET_PAGES": 100})
    """
    
    def __init__(self, prompts_dir: str = "backend/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.components: List[str] = []
        self.variables: Dict[str, Any] = {}
        
    def add_core(self, filename: str, section: Optional[str] = None) -> 'PromptBuilder':
        """Add a core reusable component to the prompt."""
        component_path = self.prompts_dir / "core" / f"{filename}.yaml"
        content = self._load_yaml_section(component_path, section)
        if content:
            self.components.append(content)
        return self
        
    def add_agent(self, filename: str, section: Optional[str] = None) -> 'PromptBuilder':
        """Add an agent-specific prompt component."""
        component_path = self.prompts_dir / "agents" / f"{filename}.yaml"
        content = self._load_yaml_section(component_path, section)
        if content:
            self.components.append(content)
        return self
        
    def add_task(self, filename: str, section: Optional[str] = None) -> 'PromptBuilder':
        """Add a task-specific prompt component."""
        component_path = self.prompts_dir / "tasks" / f"{filename}.yaml"
        content = self._load_yaml_section(component_path, section)
        if content:
            self.components.append(content)
        return self
        
    def add_custom(self, content: str) -> 'PromptBuilder':
        """Add custom text content directly."""
        self.components.append(content)
        return self
        
    def build(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """Build the final prompt with variable substitution."""
        if variables:
            self.variables.update(variables)
            
        # Join all components with appropriate spacing
        full_prompt = "\n\n".join(self.components)
        
        # Perform variable substitution
        return self._substitute_variables(full_prompt)
        
    def _load_yaml_section(self, file_path: Path, section: Optional[str] = None) -> Optional[str]:
        """Load a specific section from a YAML file."""
        try:
            if not file_path.exists():
                print(f"Warning: {file_path} not found")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if section:
                if section in data:
                    item = data[section]
                    if isinstance(item, dict):
                        title = item.get('title', '')
                        content = item.get('content', '')
                        return f"## {title}\n\n{content}" if title else content
                    return str(item)
                else:
                    print(f"Warning: Section '{section}' not found in {file_path}")
                    return None
            else:
                # Return all sections if no specific section requested
                sections = []
                for key, value in data.items():
                    if isinstance(value, dict) and 'content' in value:
                        title = value.get('title', key)
                        content = value.get('content', '')
                        sections.append(f"## {title}\n\n{content}")
                    else:
                        sections.append(str(value))
                return "\n\n".join(sections)
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
            
    def _substitute_variables(self, text: str) -> str:
        """Perform variable substitution in the text."""
        for key, value in self.variables.items():
            # Handle both {KEY} and ${KEY} formats
            text = text.replace(f"{{{key}}}", str(value))
            text = text.replace(f"${{{key}}}", str(value))
        return text


class PromptManager:
    """
    High-level prompt management for common use cases.
    Provides convenience methods for building standard prompt types.
    """
    
    def __init__(self, prompts_dir: str = "backend/prompts"):
        self.prompts_dir = prompts_dir
        
    def build_discovery_agent_prompt(self, variables: Dict[str, Any]) -> str:
        """Build complete discovery agent prompt with all necessary components."""
        return (PromptBuilder(self.prompts_dir)
                .add_core("authentication", "login_sequence")
                .add_core("blazor_patterns", "blazor_characteristics") 
                .add_core("blazor_patterns", "navigation_expansion_strategy")
                .add_core("blazor_patterns", "recursive_exploration_pattern")
                .add_core("blazor_patterns", "component_analysis_patterns")
                .add_core("blazor_patterns", "page_analysis_framework")
                .add_core("safety_rules", "exploration_safety_rules")
                .add_core("safety_rules", "error_handling_strategy")
                .add_agent("discovery_agent", "main_instructions")
                .build(variables))
                
    def build_discovery_task_description(self, variables: Dict[str, Any]) -> str:
        """Build complete discovery task description."""
        return (PromptBuilder(self.prompts_dir)
                .add_task("discovery_tasks", "explore_application")
                .add_core("blazor_patterns", "exploration_targets")
                .add_core("output_formats", "discovery_json_format")
                .build(variables))
                
    def build_validation_agent_prompt(self, variables: Dict[str, Any]) -> str:
        """Build validation agent prompt."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("validation_agent", "main_instructions")
                .add_core("output_formats", "validation_output_format")
                .build(variables))
                
    def get_agent_config(self, agent_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Get complete agent configuration with dynamic prompt building."""
        config_map = {
            "discovery": {
                "role": "Blazor Application Discovery Specialist",
                "goal": self.build_discovery_agent_goal(variables),
                "backstory": self.build_discovery_agent_backstory(variables)
            },
            "validation": {
                "role": "Discovery Validation Specialist", 
                "goal": self.build_validation_agent_goal(variables),
                "backstory": self.build_validation_agent_backstory(variables)
            },
            "pm": {
                "role": "QA Project Manager",
                "goal": self.build_pm_agent_goal(variables),
                "backstory": self.build_pm_agent_backstory(variables)
            },
            "planning": {
                "role": "Test Strategy Planning Specialist",
                "goal": self.build_planning_agent_goal(variables),
                "backstory": self.build_planning_agent_backstory(variables)
            },
            "scripting": {
                "role": "Test Automation Script Generator",
                "goal": self.build_scripting_agent_goal(variables),
                "backstory": self.build_scripting_agent_backstory(variables)
            },
            "execution": {
                "role": "Test Execution Specialist",
                "goal": self.build_execution_agent_goal(variables),
                "backstory": self.build_execution_agent_backstory(variables)
            },
            "monitor": {
                "role": "Test Execution Monitor",
                "goal": self.build_monitor_agent_goal(variables),
                "backstory": self.build_monitor_agent_backstory(variables)
            },
            "reporting": {
                "role": "Test Report Generation Specialist",
                "goal": self.build_reporting_agent_goal(variables),
                "backstory": self.build_reporting_agent_backstory(variables)
            }
        }
        return config_map.get(agent_name, {})
        
    def build_discovery_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build discovery agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("discovery_agent", "goal")
                .build(variables))
                
    def build_discovery_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build discovery agent backstory with variables.""" 
        return (PromptBuilder(self.prompts_dir)
                .add_agent("discovery_agent", "backstory")
                .build(variables))
                
    def build_validation_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build validation agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("validation_agent", "goal")  
                .build(variables))
                
    def build_validation_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build validation agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("validation_agent", "backstory")
                .build(variables))
                
    def build_pm_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build PM agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("pm_agent", "goal")
                .build(variables))
                
    def build_pm_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build PM agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("pm_agent", "backstory")
                .build(variables))
                
    def build_discovery_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build discovery task description with expected output."""
        if task_name == "discover_application":
            return {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("discovery_tasks", "discover_application")
                              .add_core("blazor_patterns", "exploration_targets") 
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "discovery_json_format")
                                  .build(variables))
            }
        elif task_name == "build_site_map":
            return {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("discovery_tasks", "build_site_map")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "sitemap_json_format")
                                  .build(variables))
            }
        return {"description": "Default task description", "expected_output": "Default expected output"}
        
    def build_validation_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build validation task description with expected output."""
        if task_name == "validate_discovery":
            return {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("validation_tasks", "validate_discovery")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "validation_output_format")
                                  .build(variables))
            }
        return {"description": "Default validation description", "expected_output": "Default validation output"}
        
    # Additional agent builder methods for all crew types
    def build_planning_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build planning agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("planning_agent", "goal")
                .build(variables))
                
    def build_planning_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build planning agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("planning_agent", "backstory")
                .build(variables))
                
    def build_scripting_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build scripting agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("scripting_agent", "goal")
                .build(variables))
                
    def build_scripting_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build scripting agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("scripting_agent", "backstory")
                .build(variables))
                
    def build_execution_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build execution agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("execution_agent", "goal")
                .build(variables))
                
    def build_execution_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build execution agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("execution_agent", "backstory")
                .build(variables))
                
    def build_monitor_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build monitor agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("monitor_agent", "goal")
                .build(variables))
                
    def build_monitor_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build monitor agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("monitor_agent", "backstory")
                .build(variables))
                
    def build_reporting_agent_goal(self, variables: Dict[str, Any]) -> str:
        """Build reporting agent goal with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("reporting_agent", "goal")
                .build(variables))
                
    def build_reporting_agent_backstory(self, variables: Dict[str, Any]) -> str:
        """Build reporting agent backstory with variables."""
        return (PromptBuilder(self.prompts_dir)
                .add_agent("reporting_agent", "backstory")
                .build(variables))

    # Task description builders for all crew types
    def build_planning_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build planning task description with expected output."""
        task_map = {
            "create_test_strategy": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("planning_tasks", "create_test_strategy")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "test_strategy_format")
                                  .build(variables))
            },
            "design_test_scenarios": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("planning_tasks", "design_test_scenarios")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "test_scenarios_format")
                                  .build(variables))
            }
        }
        return task_map.get(task_name, {"description": "Default planning task", "expected_output": "Default planning output"})
    
    def build_scripting_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build scripting task description with expected output."""
        task_map = {
            "generate_test_scripts": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("scripting_tasks", "generate_test_scripts")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "test_scripts_format")
                                  .build(variables))
            }
        }
        return task_map.get(task_name, {"description": "Default scripting task", "expected_output": "Default scripting output"})
    
    def build_execution_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build execution task description with expected output."""
        task_map = {
            "execute_test_suite": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("execution_tasks", "execute_test_suite")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "execution_results_format")
                                  .build(variables))
            }
        }
        return task_map.get(task_name, {"description": "Default execution task", "expected_output": "Default execution output"})
    
    def build_monitoring_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build monitoring task description with expected output."""
        task_map = {
            "monitor_execution": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("execution_tasks", "monitor_execution")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "monitoring_report_format")
                                  .build(variables))
            }
        }
        return task_map.get(task_name, {"description": "Default monitoring task", "expected_output": "Default monitoring output"})
    
    def build_reporting_task_description(self, task_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Build reporting task description with expected output."""
        task_map = {
            "generate_test_report": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("reporting_tasks", "generate_test_report")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "comprehensive_report_format")
                                  .build(variables))
            },
            "create_executive_summary": {
                "description": (PromptBuilder(self.prompts_dir)
                              .add_task("reporting_tasks", "stakeholder_communication")
                              .build(variables)),
                "expected_output": (PromptBuilder(self.prompts_dir)
                                  .add_core("output_formats", "executive_summary_format")
                                  .build(variables))
            }
        }
        return task_map.get(task_name, {"description": "Default reporting task", "expected_output": "Default reporting output"})
        
    def get_core_component(self, component_name: str) -> Dict[str, Any]:
        """Get a core component by name."""
        try:
            component_path = Path(self.prompts_dir) / "core" / f"{component_name}.yaml"
            if component_path.exists():
                with open(component_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file) or {}
            else:
                print(f"Warning: Core component {component_name} not found")
                return {"content": {"mandatory_instructions": ""}}
        except Exception as e:
            print(f"Error loading core component {component_name}: {e}")
            return {"content": {"mandatory_instructions": ""}}


# Example usage and testing functions
def test_prompt_builder():
    """Test the prompt builder functionality."""
    print("Testing PromptBuilder...")
    
    variables = {
        "BASE_URL": "https://example.com",
        "USERNAME": "testuser",
        "PASSWORD": "testpass",
        "TARGET_PAGES": 100,
        "HEADLESS": "false"
    }
    
    # Test building discovery agent prompt
    builder = PromptBuilder()
    prompt = (builder
              .add_core("authentication", "login_sequence")
              .add_core("blazor_patterns", "navigation_expansion_strategy")
              .add_core("safety_rules", "exploration_safety_rules")
              .build(variables))
    
    print("Built prompt length:", len(prompt))
    print("First 200 characters:", prompt[:200])
    
    # Test using PromptManager
    manager = PromptManager()
    discovery_prompt = manager.build_discovery_agent_prompt(variables)
    print("\\nDiscovery agent prompt length:", len(discovery_prompt))


def get_known_menu_inventory():
    with open("backend/prompts/data/known_menu_inventory.yaml", "r") as file:
        return yaml.safe_load(file).get("known_menu_inventory", {})

if __name__ == "__main__":
    test_prompt_builder()

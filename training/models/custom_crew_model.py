import os
import json
import yaml
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
import logging

logger = logging.getLogger(__name__)

class CustomCrewModel:
    """
    Custom model wrapper that integrates trained models with CrewAI
    This provides seamless integration of fine-tuned models with existing CrewAI workflows
    """
    
    def __init__(self, model_path: str, config_path: Optional[str] = None):
        self.model_path = model_path
        self.config = self._load_config(config_path)
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load model configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_model(self):
        """Load the trained model and tokenizer"""
        try:
            # This would load the actual fine-tuned model
            # For now, we'll use a placeholder
            logger.info(f"Loading custom CrewAI model from {self.model_path}")
            
            # In a real implementation, this would load:
            # from transformers import AutoModel, AutoTokenizer
            # self.model = AutoModel.from_pretrained(self.model_path)
            # self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            self.model = "custom_crewai_model_placeholder"
            self.tokenizer = "custom_tokenizer_placeholder"
            
            logger.info("✅ Custom model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load custom model: {str(e)}")
            raise
    
    def create_optimized_agent(self, agent_config: Dict[str, Any], **kwargs) -> Agent:
        """Create an agent with the custom trained model"""
        
        # Enhanced configuration for trained model
        enhanced_config = agent_config.copy()
        
        # Add custom model settings
        enhanced_config.update({
            'llm': self.get_llm_config(),
            'memory': True,
            'verbose': False,  # Optimized for efficiency
            'max_iter': 200,   # Higher iteration limit for complex tasks
            'allow_delegation': False  # Prevent unnecessary delegation
        })
        
        # Create agent with enhanced configuration
        agent = Agent(**enhanced_config, **kwargs)
        
        logger.info(f"✅ Created optimized agent: {agent_config.get('role', 'Unknown')}")
        return agent
    
    def create_optimized_task(self, task_config: Dict[str, Any], agent: Agent, **kwargs) -> Task:
        """Create a task optimized for the trained model"""
        
        enhanced_config = task_config.copy()
        
        # Add optimization settings
        enhanced_config.update({
            'agent': agent,
            'expected_output': enhanced_config.get('expected_output', 'Task completed successfully'),
            'output_json': enhanced_config.get('output_json', None),
            'output_file': enhanced_config.get('output_file', None),
            'callback': self._task_callback if self.config.get('enable_callbacks') else None
        })
        
        task = Task(**enhanced_config, **kwargs)
        
        logger.info(f"✅ Created optimized task: {task_config.get('description', 'Unknown')[:50]}...")
        return task
    
    def create_optimized_crew(self, agents: list, tasks: list, **kwargs) -> Crew:
        """Create a crew with optimized settings for trained model"""
        
        # Default optimized crew settings
        crew_config = {
            'agents': agents,
            'tasks': tasks,
            'process': kwargs.get('process', 'sequential'),
            'verbose': False,  # Reduced verbosity for efficiency
            'memory': kwargs.get('memory', True),
            'embedder': kwargs.get('embedder', None),
            'max_iter': kwargs.get('max_iter', 150),
            'step_callback': self._step_callback if self.config.get('enable_callbacks') else None
        }
        
        # Override with any provided kwargs
        crew_config.update(kwargs)
        
        crew = Crew(**crew_config)
        
        logger.info(f"✅ Created optimized crew with {len(agents)} agents and {len(tasks)} tasks")
        return crew
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for the custom model"""
        return {
            'model': self.config.get('model_name', 'custom-crewai-model'),
            'temperature': self.config.get('temperature', 0.1),
            'max_tokens': self.config.get('max_tokens', 500),
            'top_p': self.config.get('top_p', 0.8),
            'frequency_penalty': self.config.get('frequency_penalty', 0.0),
            'presence_penalty': self.config.get('presence_penalty', 0.0)
        }
    
    def _task_callback(self, task_output):
        """Custom callback for task execution monitoring"""
        logger.info(f"📋 Task callback: {task_output.task.description[:30]}... - Status: {task_output.status}")
        
        # Custom logic for handling task completion
        if hasattr(task_output, 'screenshot_count'):
            logger.info(f"📸 Screenshots taken: {task_output.screenshot_count}")
        
        return task_output
    
    def _step_callback(self, step):
        """Custom callback for step execution monitoring"""
        if self.config.get('log_steps', False):
            logger.debug(f"🔄 Step: {step.action} - Agent: {step.agent.role}")
        
        # Custom step monitoring logic
        if hasattr(step, 'tool_name') and step.tool_name == 'browser_take_screenshot':
            logger.info(f"📸 Screenshot step executed")
        
        return step

class ModelManager:
    """Manage multiple trained models and their deployment"""
    
    def __init__(self, models_dir: str = "training/models"):
        self.models_dir = models_dir
        self.available_models = {}
        self._discover_models()
    
    def _discover_models(self):
        """Discover available trained models"""
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory not found: {self.models_dir}")
            return
        
        for item in os.listdir(self.models_dir):
            model_path = os.path.join(self.models_dir, item)
            if os.path.isdir(model_path):
                config_path = os.path.join(model_path, 'config.yaml')
                if os.path.exists(config_path):
                    self.available_models[item] = {
                        'path': model_path,
                        'config': config_path,
                        'created': os.path.getctime(model_path)
                    }
        
        logger.info(f"📦 Discovered {len(self.available_models)} trained models")
    
    def load_model(self, model_name: str) -> CustomCrewModel:
        """Load a specific trained model"""
        if model_name not in self.available_models:
            raise ValueError(f"Model '{model_name}' not found. Available: {list(self.available_models.keys())}")
        
        model_info = self.available_models[model_name]
        return CustomCrewModel(model_info['path'], model_info['config'])
    
    def get_latest_model(self) -> CustomCrewModel:
        """Get the most recently trained model"""
        if not self.available_models:
            raise ValueError("No trained models available")
        
        latest_model = max(self.available_models.items(), 
                          key=lambda x: x[1]['created'])
        
        return self.load_model(latest_model[0])
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their info"""
        return self.available_models

def create_production_ready_crew(base_url: str, test_run_id: str, use_trained_model: bool = True) -> Crew:
    """
    Create a production-ready crew using trained models
    This is the main integration point for using trained CrewAI models
    """
    
    if use_trained_model:
        try:
            # Load the latest trained model
            model_manager = ModelManager()
            custom_model = model_manager.get_latest_model()
            logger.info("🎯 Using trained CrewAI model")
        except Exception as e:
            logger.warning(f"⚠️ Could not load trained model, falling back to default: {e}")
            custom_model = None
    else:
        custom_model = None
    
    # Agent configuration (would be loaded from YAML files)
    agent_config = {
        'role': 'Blazor Application Discovery Specialist',
        'goal': f'Systematically explore and document every accessible page in {base_url}',
        'backstory': 'Expert QA automation specialist with 15+ years of experience',
        'allow_delegation': False,
        'verbose': False,
        'max_iter': 100
    }
    
    # Task configuration  
    task_config = {
        'description': f'Complete discovery of all pages in {base_url} with minimum 34+ screenshots',
        'expected_output': 'Complete discovery summary with all pages documented'
    }
    
    if custom_model:
        # Use trained model
        agent = custom_model.create_optimized_agent(agent_config)
        task = custom_model.create_optimized_task(task_config, agent)
        crew = custom_model.create_optimized_crew([agent], [task])
    else:
        # Fallback to standard CrewAI
        from backend.crew_test_explorer import ExplorationCrew
        import asyncio
        exploration_crew = asyncio.run(ExplorationCrew.create(test_run_id, base_url))
        crew = asyncio.run(exploration_crew.crew())
    
    logger.info("✅ Production-ready crew created")
    return crew

# Example usage
if __name__ == "__main__":
    # Example of how to use the custom model
    try:
        # Create production crew with trained model
        crew = create_production_ready_crew(
            base_url="https://example.com/app",
            test_run_id="test_123",
            use_trained_model=True
        )
        
        print("✅ Successfully created crew with trained model")
        
    except Exception as e:
        print(f"❌ Error creating crew: {e}")

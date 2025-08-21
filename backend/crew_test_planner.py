import logging
from typing import List
import warnings
import pandas as pd

from backend.helpers.socket_log_handler import WebSocketLogHandler
from backend.helpers.socket_manager import SocketManager
from backend.prompts.prompt_builder import PromptManager

# Suppress Pydantic and general deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import MCPServerAdapter
from crewai_tools import FileWriterTool
from crewai_tools import FileReadTool
from mcp import StdioServerParameters
import os
from pathlib import Path
from dotenv import load_dotenv
from crewai_tools import FileReadTool,FileWriterTool,DirectoryReadTool


class TestPlanningCrew():
    """
    Test Planning Crew - Phase 2 of the testing pipeline
    
    Responsibilities:
    - Analyze discovery results and create comprehensive test strategy
    - Design test scenarios and prioritize testing activities
    - Validate test coverage and planning quality
    """
    
    agents: List[Agent]
    tasks: List[Task]
    socket_manager: SocketManager = None
    force: bool = False
    test_run_id: str = ""
    base_url: str = ""

    def __init__(self, test_run_id, base_url=""):
        # Initialize all attributes first
        self.tools = []
        self.test_run_id = test_run_id
        self.base_url = base_url
        self.agents = []
        self.tasks = []
        
        # Initialize the new prompt management system
        self.prompt_manager = PromptManager()
        
        self.set_environment_variables()

    @classmethod
    async def create(cls, test_run_id, base_url=""):
        try:
            env_path = "backend//.env"
            load_dotenv(dotenv_path=env_path)
            
            # Create a new instance properly with base_url
            instance = cls(test_run_id, base_url)
            
            # Setup tools asynchronously
            instance.tools = await instance.setup_tools()

            # Create agents and tasks after tools are setup
            print(f"Creating planning agents for test_run_id: {test_run_id}")
            instance.create_agents()
            print(f"Planning agents created: {len(instance.agents)}")
            
            instance.create_tasks()
            print(f"Planning tasks created: {len(instance.tasks)}")

            return instance
        except Exception as e:
            print(f"Error in TestPlanningCrew.create: {e}")
            raise

    def set_environment_variables(self):
        # Set environment variables with default values if not present
        azure_api_base = os.getenv("AZURE_API_BASE")
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_api_version = os.getenv("AZURE_API_VERSION")
        
        if azure_api_base:
            os.environ['AZURE_DEPLOYMENT_TARGET_URL'] = azure_api_base
        else:
            print("Warning: AZURE_API_BASE not set in environment")
            
        if azure_api_key:
            os.environ['AZURE_API_KEY'] = azure_api_key
        else:
            print("Warning: AZURE_API_KEY not set in environment")
            
        if azure_api_version:
            os.environ['AZURE_API_VERSION'] = azure_api_version
        else:
            print("Warning: AZURE_API_VERSION not set in environment")
            
        self.azure_llm = "azure/gpt-4.1"

    async def setup_tools(self):
        self.tools = [FileReadTool(), FileWriterTool(), DirectoryReadTool()]
        
        mcp_tools = await self._setup_mcp_servers()
        self.tools.extend(mcp_tools)
        return self.tools

    def create_agents(self):
        # Prepare prompt variables
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}'
        }

        # Create Test Planning Agent using new prompt system
        planning_config = self.prompt_manager.get_agent_config('planning', prompt_vars)
        self.test_planner_agent = Agent(
            role=planning_config.get('role', 'Test Planning Specialist'),
            goal=planning_config.get('goal', 'Design comprehensive test strategy and scenarios'),
            backstory=planning_config.get('backstory', 'Expert test strategist and planner'),
            llm=self.azure_llm,
            tools=self.tools,
            verbose=True
        )

        # Create Validation Agent for quality assurance
        validation_config = self.prompt_manager.get_agent_config('validation', prompt_vars)
        self.validation_agent = Agent(
            role=validation_config.get('role', 'Planning Validation Specialist'),
            goal=validation_config.get('goal', 'Validate test planning quality and coverage'),
            backstory=validation_config.get('backstory', 'Quality assurance expert'),
            llm=self.azure_llm,
            verbose=True
        )

        self.agents = [self.test_planner_agent, self.validation_agent]
        print(f"✅ Planning agents created using new prompt system")

    def create_tasks(self):
        # Prepare prompt variables for tasks
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}',
            'DISCOVERY_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/discovery_summary.json',
            'SITEMAP_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/site_map.json',
            'TEST_PLAN_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/test_plan.json',
            'TEST_SCENARIOS_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/test_scenarios.json'
        }

        # Create test strategy planning task
        strategy_task = self.prompt_manager.build_planning_task_description('create_test_strategy', prompt_vars)
        create_test_strategy = Task(
            description=strategy_task.get('description', 'Analyze discovery results and create comprehensive test strategy'),
            expected_output=strategy_task.get('expected_output', 'Detailed test strategy document'),
            agent=self.test_planner_agent,
            output_file=prompt_vars['TEST_PLAN_OUTPUT_FILE']
        )

        # Create test scenarios design task
        scenarios_task = self.prompt_manager.build_planning_task_description('design_test_scenarios', prompt_vars)
        design_test_scenarios = Task(
            description=scenarios_task.get('description', 'Design detailed test scenarios based on strategy'),
            expected_output=scenarios_task.get('expected_output', 'Comprehensive test scenarios'),
            agent=self.test_planner_agent,
            context=[create_test_strategy],
            output_file=prompt_vars['TEST_SCENARIOS_OUTPUT_FILE']
        )

        # Create planning validation task
        validation_task = self.prompt_manager.build_validation_task_description('validate_test_plan', prompt_vars)
        validate_test_plan = Task(
            description=validation_task.get('description', 'Validate test planning completeness and quality'),
            expected_output=validation_task.get('expected_output', 'Test plan validation report'),
            context=[design_test_scenarios],
            agent=self.validation_agent
        )
        
        self.tasks = [create_test_strategy, design_test_scenarios, validate_test_plan]
        print(f"✅ Planning tasks created using new prompt system")

    async def crew(self, base_url=None) -> Crew:
        logging.info("Initializing test planning crew...")
        
        # Use provided base_url or fall back to instance base_url
        if base_url:
            self.base_url = base_url
        elif not self.base_url:
            print("⚠️ Warning: No base URL provided for planning crew")

        # Use all agents and tasks for phase-based execution
        filtered_agents = self.agents
        filtered_tasks = self.tasks
        
        logging.info(f"Using all planning agents: {[getattr(a, 'role', 'Unknown') for a in filtered_agents]}")
        
        if len(filtered_agents) == 0:
            raise Exception('No planning agents available')

        logging.info("Planning agents and tasks loaded.")

        # Get system-level instructions from new prompt system
        mandatory_instructions = self.prompt_manager.get_core_component('safety_rules')
        instructions = mandatory_instructions.get('content', {}).get('mandatory_instructions', '')
        print("✅ Using planning instructions from new prompt system")

        return Crew(
            agents=filtered_agents,
            tasks=filtered_tasks,
            llm=self.azure_llm,
            tools=self.tools,
            process=Process.sequential,
            verbose=True,
            telemetry=False,
            output_log_file=self.getTaskOutFilePath('planning_crew_output.log'),
            output_dir=f'backend/fs_files/{self.test_run_id}',
        )

    async def wait_for_page_load(self, tool_map, timeout_sec=30):
        # Planning crew doesn't need browser interaction
        print("✅ Planning crew - no browser interaction required")
        return

    def set_test_run_id(self, test_run_id: str):
        self.test_run_id = test_run_id

    def set_base_url(self, base_url: str):
        """Update the base URL for the application being tested"""
        self.base_url = base_url
        print(f"✅ Planning crew base URL updated to: {base_url}")
        
        # Recreate agents and tasks with updated URL if they exist
        if hasattr(self, 'agents') and self.agents:
            print("🔄 Recreating planning agents with updated URL...")
            self.create_agents()
        
        if hasattr(self, 'tasks') and self.tasks:
            print("🔄 Recreating planning tasks with updated URL...")
            self.create_tasks()

    def set_socket_manager(self, socket_manager):
        self.socket_manager = socket_manager
        
        if self.socket_manager:
            ws_handler = WebSocketLogHandler(self.socket_manager, source="TestPlanningCrew")
            ws_handler.setLevel(logging.INFO)
            ws_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
            
            if not any(isinstance(h, WebSocketLogHandler) for h in logging.getLogger().handlers):
                logging.getLogger().addHandler(ws_handler)

    def getTaskOutFilePath(self, filename: str):
        return f'backend/fs_files/{self.test_run_id}/{filename}'
  
    async def emit_log(self, message: str):
        if self.socket_manager:
            await self.socket_manager.broadcast({
                "type": "log",
                "source": self.__class__.__name__,
                "message": message
            })

    def get_tool_map(self, tools):
        return {getattr(tool, 'name', tool.__class__.__name__): tool for tool in tools or []}

    async def _setup_mcp_servers(self):
        try:
            env = os.environ.copy()
            env['BROWSER'] = 'msedge'
            env['PLAYWRIGHT_BROWSER'] = 'msedge'
            mcp_params = [StdioServerParameters(command="npx", args=["-y", "@playwright/mcp"], env=env)]
            tools = MCPServerAdapter(mcp_params).tools
            return tools
        except Exception as e:
            await self.emit_log(f"MCP setup failed for planning crew: {e}")
            return []

    def get_cost(self):
        if hasattr(self, 'crew'):
            costs = 0.150 * (self.crew.usage_metrics.prompt_tokens + self.crew.usage_metrics.completion_tokens) / 1_000_000
            print(f"Test Planning Crew total costs: ${costs:.4f}")

            try:
                df_usage_metrics = pd.DataFrame([self.crew.usage_metrics.dict()])
                return df_usage_metrics
            except Exception:
                return self.crew.usage_metrics.dict()
        return {"message": "No crew execution data available"}
    
    def get_prompt_system_status(self):
        """Get status information about the prompt management system"""
        try:
            status = {
                'prompt_manager_initialized': hasattr(self, 'prompt_manager'),
                'base_url': self.base_url,
                'test_run_id': self.test_run_id,
                'crew_type': 'TestPlanningCrew',
                'agents_count': len(self.agents) if hasattr(self, 'agents') else 0,
                'tasks_count': len(self.tasks) if hasattr(self, 'tasks') else 0
            }
            return status
        except Exception as e:
            return {'error': str(e), 'prompt_system_available': False}

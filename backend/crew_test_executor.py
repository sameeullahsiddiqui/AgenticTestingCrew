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


class TestExecutionCrew():
    """
    Test Execution Crew - Phase 3 of the testing pipeline
    
    Responsibilities:
    - Generate executable test scripts from test scenarios
    - Execute automated tests with real-time monitoring
    - Collect test results and evidence
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
            print(f"Creating execution agents for test_run_id: {test_run_id}")
            instance.create_agents()
            print(f"Execution agents created: {len(instance.agents)}")
            
            instance.create_tasks()
            print(f"Execution tasks created: {len(instance.tasks)}")

            return instance
        except Exception as e:
            print(f"Error in TestExecutionCrew.create: {e}")
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

        # Create Test Scripting Agent using new prompt system
        scripting_config = self.prompt_manager.get_agent_config('scripting', prompt_vars)
        self.test_script_agent = Agent(
            role=scripting_config.get('role', 'Test Script Generator'),
            goal=scripting_config.get('goal', 'Generate executable test automation scripts'),
            backstory=scripting_config.get('backstory', 'Expert test automation engineer'),
            llm=self.azure_llm,
            tools=self.tools,
            verbose=True
        )

        # Create Test Execution Agent using new prompt system
        execution_config = self.prompt_manager.get_agent_config('execution', prompt_vars)
        self.test_executor_agent = Agent(
            role=execution_config.get('role', 'Test Execution Specialist'),
            goal=execution_config.get('goal', 'Execute automated tests and collect results'),
            backstory=execution_config.get('backstory', 'Experienced test execution expert'),
            llm=self.azure_llm,
            tools=self.tools,
            verbose=True
        )

        # Create Monitoring Agent for real-time oversight
        monitoring_config = self.prompt_manager.get_agent_config('monitor', prompt_vars)
        self.monitor_agent = Agent(
            role=monitoring_config.get('role', 'Test Execution Monitor'),
            goal=monitoring_config.get('goal', 'Monitor test execution and handle issues'),
            backstory=monitoring_config.get('backstory', 'Real-time monitoring specialist'),
            llm=self.azure_llm,
            verbose=True
        )

        self.agents = [self.test_script_agent, self.test_executor_agent, self.monitor_agent]
        print(f"✅ Execution agents created using new prompt system")

    def create_tasks(self):
        # Prepare prompt variables for tasks
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}',
            'TEST_SCENARIOS_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/test_scenarios.json',
            'TEST_SCRIPTS_OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}/test_scripts',
            'TEST_RESULTS_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/test_results.json',
            'EXECUTION_LOG_FILE': f'backend/fs_files/{self.test_run_id}/execution.log'
        }

        # Create test script generation task
        scripting_task = self.prompt_manager.build_scripting_task_description('generate_test_scripts', prompt_vars)
        generate_test_scripts = Task(
            description=scripting_task.get('description', 'Generate executable test scripts from scenarios'),
            expected_output=scripting_task.get('expected_output', 'Complete test automation scripts'),
            agent=self.test_script_agent,
            output_file=f"{prompt_vars['TEST_SCRIPTS_OUTPUT_DIR']}/generated_scripts.json"
        )

        # Create test execution task
        execution_task = self.prompt_manager.build_execution_task_description('execute_test_suite', prompt_vars)
        execute_test_suite = Task(
            description=execution_task.get('description', 'Execute automated test suite with monitoring'),
            expected_output=execution_task.get('expected_output', 'Complete test execution results'),
            agent=self.test_executor_agent,
            context=[generate_test_scripts],
            output_file=prompt_vars['TEST_RESULTS_OUTPUT_FILE']
        )

        # Create monitoring and recovery task
        monitoring_task = self.prompt_manager.build_monitoring_task_description('monitor_execution', prompt_vars)
        monitor_execution = Task(
            description=monitoring_task.get('description', 'Monitor test execution and handle failures'),
            expected_output=monitoring_task.get('expected_output', 'Execution monitoring report'),
            agent=self.monitor_agent,
            context=[execute_test_suite],
            output_file=prompt_vars['EXECUTION_LOG_FILE']
        )
        
        self.tasks = [generate_test_scripts, execute_test_suite, monitor_execution]
        print(f"✅ Execution tasks created using new prompt system")

    async def crew(self, base_url=None) -> Crew:
        logging.info("Initializing test execution crew...")
        
        # Use provided base_url or fall back to instance base_url
        if base_url:
            self.base_url = base_url
        elif not self.base_url:
            print("⚠️ Warning: No base URL provided for execution crew")

        tool_map = self.get_tool_map(self.tools)
        navigate_tool = tool_map.get('browser_navigate')

        if navigate_tool and self.base_url:
            print(f"🔗 Execution crew navigating to: {self.base_url}")
            navigate_tool._run(url=self.base_url)
            await self.wait_for_page_load(tool_map)

        # Use all agents and tasks for phase-based execution
        filtered_agents = self.agents
        filtered_tasks = self.tasks
        
        logging.info(f"Using all execution agents: {[getattr(a, 'role', 'Unknown') for a in filtered_agents]}")
        
        if len(filtered_agents) == 0:
            raise Exception('No execution agents available')

        logging.info("Execution agents and tasks loaded.")

        # Get system-level instructions from new prompt system
        mandatory_instructions = self.prompt_manager.get_core_component('safety_rules')
        instructions = mandatory_instructions.get('content', {}).get('mandatory_instructions', '')
        print("✅ Using execution instructions from new prompt system")

        return Crew(
            agents=filtered_agents,
            tasks=filtered_tasks,
            llm=self.azure_llm,
            tools=self.tools,
            process=Process.sequential,
            verbose=True,
            telemetry=False,
            output_log_file=self.getTaskOutFilePath('execution_crew_output.log'),
            output_dir=f'backend/fs_files/{self.test_run_id}',
        )

    async def wait_for_page_load(self, tool_map, timeout_sec=30):
        wait_tool = tool_map.get('browser_wait_for')
        if wait_tool:
            for cond in [{"textGone": "Loading"}, {"text": "Sign in"}, {"text": "Continue"}]:
                try:
                    wait_tool._run(time=timeout_sec, **cond)
                    print(f"⏳ Execution crew wait condition satisfied: {cond}")
                    return
                except Exception:
                    continue
        print("⚠️ Execution crew page load wait conditions not confirmed; proceeding anyway")

    def set_test_run_id(self, test_run_id: str):
        self.test_run_id = test_run_id

    def set_base_url(self, base_url: str):
        """Update the base URL for the application being tested"""
        self.base_url = base_url
        print(f"✅ Execution crew base URL updated to: {base_url}")
        
        # Recreate agents and tasks with updated URL if they exist
        if hasattr(self, 'agents') and self.agents:
            print("🔄 Recreating execution agents with updated URL...")
            self.create_agents()
        
        if hasattr(self, 'tasks') and self.tasks:
            print("🔄 Recreating execution tasks with updated URL...")
            self.create_tasks()

    def set_socket_manager(self, socket_manager):
        self.socket_manager = socket_manager
        
        if self.socket_manager:
            ws_handler = WebSocketLogHandler(self.socket_manager, source="TestExecutionCrew")
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
            await self.emit_log(f"MCP setup failed for execution crew: {e}")
            raise e

    def get_cost(self):
        if hasattr(self, 'crew'):
            costs = 0.150 * (self.crew.usage_metrics.prompt_tokens + self.crew.usage_metrics.completion_tokens) / 1_000_000
            print(f"Test Execution Crew total costs: ${costs:.4f}")

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
                'crew_type': 'TestExecutionCrew',
                'agents_count': len(self.agents) if hasattr(self, 'agents') else 0,
                'tasks_count': len(self.tasks) if hasattr(self, 'tasks') else 0
            }
            return status
        except Exception as e:
            return {'error': str(e), 'prompt_system_available': False}

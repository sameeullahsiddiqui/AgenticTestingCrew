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


class TestReportingCrew():
    """
    Test Reporting Crew - Phase 4 of the testing pipeline
    
    Responsibilities:
    - Analyze all test execution results and evidence
    - Generate comprehensive stakeholder reports
    - Provide actionable recommendations and insights
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
            print(f"Creating reporting agents for test_run_id: {test_run_id}")
            instance.create_agents()
            print(f"Reporting agents created: {len(instance.agents)}")
            
            instance.create_tasks()
            print(f"Reporting tasks created: {len(instance.tasks)}")

            return instance
        except Exception as e:
            print(f"Error in TestReportingCrew.create: {e}")
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
        
        # Reporting crew typically doesn't need browser tools, but include for completeness
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

        # Create Reporting Agent using new prompt system
        reporting_config = self.prompt_manager.get_agent_config('reporting', prompt_vars)
        self.test_reporter_agent = Agent(
            role=reporting_config.get('role', 'Test Report Specialist'),
            goal=reporting_config.get('goal', 'Generate comprehensive test reports and insights'),
            backstory=reporting_config.get('backstory', 'Expert test analyst and report writer'),
            llm=self.azure_llm,
            tools=self.tools,
            verbose=True
        )

        # Create Quality Assurance Agent for report validation
        validation_config = self.prompt_manager.get_agent_config('validation', prompt_vars)
        self.report_validator_agent = Agent(
            role=validation_config.get('role', 'Report Quality Assurance'),
            goal=validation_config.get('goal', 'Validate report quality and completeness'),
            backstory=validation_config.get('backstory', 'Quality assurance and communication expert'),
            llm=self.azure_llm,
            verbose=True
        )

        self.agents = [self.test_reporter_agent, self.report_validator_agent]
        print(f"✅ Reporting agents created using new prompt system")

    def create_tasks(self):
        # Prepare prompt variables for tasks
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}',
            'TEST_RESULTS_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/test_results.json',
            'EXECUTION_LOG_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/execution.log',
            'DISCOVERY_INPUT_FILE': f'backend/fs_files/{self.test_run_id}/discovery_summary.json',
            'FINAL_REPORT_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/final_test_report.md',
            'EXECUTIVE_SUMMARY_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/executive_summary.md'
        }

        # Create comprehensive report generation task
        report_task = self.prompt_manager.build_reporting_task_description('generate_test_report', prompt_vars)
        generate_comprehensive_report = Task(
            description=report_task.get('description', 'Analyze all test results and generate comprehensive report'),
            expected_output=report_task.get('expected_output', 'Complete test analysis report'),
            agent=self.test_reporter_agent,
            output_file=prompt_vars['FINAL_REPORT_OUTPUT_FILE']
        )

        # Create executive summary task
        summary_task = self.prompt_manager.build_reporting_task_description('create_executive_summary', prompt_vars)
        create_executive_summary = Task(
            description=summary_task.get('description', 'Create executive summary for stakeholders'),
            expected_output=summary_task.get('expected_output', 'Executive summary with key insights'),
            agent=self.test_reporter_agent,
            context=[generate_comprehensive_report],
            output_file=prompt_vars['EXECUTIVE_SUMMARY_OUTPUT_FILE']
        )

        # Create report validation task
        validation_task = self.prompt_manager.build_validation_task_description('validate_final_report', prompt_vars)
        validate_final_report = Task(
            description=validation_task.get('description', 'Validate final report quality and completeness'),
            expected_output=validation_task.get('expected_output', 'Report validation and quality assessment'),
            context=[create_executive_summary],
            agent=self.report_validator_agent
        )
        
        self.tasks = [generate_comprehensive_report, create_executive_summary, validate_final_report]
        print(f"✅ Reporting tasks created using new prompt system")

    async def crew(self, base_url=None) -> Crew:
        logging.info("Initializing test reporting crew...")
        
        # Use provided base_url or fall back to instance base_url
        if base_url:
            self.base_url = base_url
        elif not self.base_url:
            print("⚠️ Warning: No base URL provided for reporting crew")

        # Use all agents and tasks for phase-based execution
        filtered_agents = self.agents
        filtered_tasks = self.tasks
        
        logging.info(f"Using all reporting agents: {[getattr(a, 'role', 'Unknown') for a in filtered_agents]}")
        
        if len(filtered_agents) == 0:
            raise Exception('No reporting agents available')

        logging.info("Reporting agents and tasks loaded.")

        # Get system-level instructions from new prompt system
        mandatory_instructions = self.prompt_manager.get_core_component('safety_rules')
        instructions = mandatory_instructions.get('content', {}).get('mandatory_instructions', '')
        print("✅ Using reporting instructions from new prompt system")

        return Crew(
            agents=filtered_agents,
            tasks=filtered_tasks,
            llm=self.azure_llm,
            tools=self.tools,
            process=Process.sequential,
            verbose=True,
            telemetry=False,
            output_log_file=self.getTaskOutFilePath('reporting_crew_output.log'),
            output_dir=f'backend/fs_files/{self.test_run_id}',
        )

    async def wait_for_page_load(self, tool_map, timeout_sec=30):
        # Reporting crew doesn't need browser interaction
        print("✅ Reporting crew - no browser interaction required")
        return

    def set_test_run_id(self, test_run_id: str):
        self.test_run_id = test_run_id

    def set_base_url(self, base_url: str):
        """Update the base URL for the application being tested"""
        self.base_url = base_url
        print(f"✅ Reporting crew base URL updated to: {base_url}")
        
        # Recreate agents and tasks with updated URL if they exist
        if hasattr(self, 'agents') and self.agents:
            print("🔄 Recreating reporting agents with updated URL...")
            self.create_agents()
        
        if hasattr(self, 'tasks') and self.tasks:
            print("🔄 Recreating reporting tasks with updated URL...")
            self.create_tasks()

    def set_socket_manager(self, socket_manager):
        self.socket_manager = socket_manager
        
        if self.socket_manager:
            ws_handler = WebSocketLogHandler(self.socket_manager, source="TestReportingCrew")
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
            await self.emit_log(f"MCP setup failed for reporting crew (this is normal for reporting): {e}")
            return []

    def get_cost(self):
        if hasattr(self, 'crew'):
            costs = 0.150 * (self.crew.usage_metrics.prompt_tokens + self.crew.usage_metrics.completion_tokens) / 1_000_000
            print(f"Test Reporting Crew total costs: ${costs:.4f}")

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
                'crew_type': 'TestReportingCrew',
                'agents_count': len(self.agents) if hasattr(self, 'agents') else 0,
                'tasks_count': len(self.tasks) if hasattr(self, 'tasks') else 0
            }
            return status
        except Exception as e:
            return {'error': str(e), 'prompt_system_available': False}

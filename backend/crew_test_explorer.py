import os
import logging
from pandas import pd
import warnings
from typing import List
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool, FileWriterTool, DirectoryReadTool, MCPServerAdapter
from mcp import StdioServerParameters
from backend.helpers.socket_log_handler import WebSocketLogHandler
from backend.helpers.socket_manager import SocketManager
from backend.prompts.prompt_builder import PromptManager

warnings.filterwarnings("ignore", category=DeprecationWarning)

class ExplorationCrew:
    def __init__(self, test_run_id: str, base_url: str = ""):
        self.test_run_id = test_run_id
        self.base_url = base_url
        self.agents: List[Agent] = []
        self.tasks: List[Task] = []
        self.tools = []
        self.socket_manager: SocketManager = None
        self.prompt_manager = PromptManager()
        self.set_environment_variables()

    @classmethod
    async def create(cls, test_run_id: str, base_url: str = ""):
        load_dotenv(dotenv_path="backend/.env")
        instance = cls(test_run_id, base_url)
        instance.tools = await instance.setup_tools()
        instance.create_agents()
        instance.create_tasks()
        return instance

    def set_environment_variables(self):
        load_dotenv(dotenv_path="backend/.env")
        os.environ['AZURE_DEPLOYMENT_TARGET_URL'] = os.getenv("AZURE_API_BASE", "")
        os.environ['AZURE_API_KEY'] = os.getenv("AZURE_API_KEY", "")
        os.environ['AZURE_API_VERSION'] = os.getenv("AZURE_API_VERSION", "")        
        self.azure_llm = "azure/gpt-4.1"
    async def setup_tools(self):
        tools = [FileReadTool(), FileWriterTool(), DirectoryReadTool()]
        env = os.environ.copy()
        env['BROWSER'] = 'msedge'
        env['PLAYWRIGHT_BROWSER'] = 'msedge'
        mcp_params = [StdioServerParameters(command="npx", args=["-y", "@playwright/mcp"], env=env)]
        tools += MCPServerAdapter(mcp_params).tools
        return tools

    def create_agents(self):
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}'
        }

        self.discovery_agent = Agent(**self.prompt_manager.get_agent_config('discovery', prompt_vars), tools=self.tools, verbose=True)
        self.agents = [self.discovery_agent]

    def create_tasks(self):
        prompt_vars = {
            'BASE_URL': self.base_url,
            'TEST_RUN_ID': self.test_run_id,
            'OUTPUT_DIR': f'backend/fs_files/{self.test_run_id}',
            'TARGET_PAGE_COUNT': 100,
            'DISCOVERY_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/discovery_summary.json',
            'SITEMAP_OUTPUT_FILE': f'backend/fs_files/{self.test_run_id}/site_map.json'
        }

        # OPTIMIZATION: Single task instead of 3 separate tasks to reduce LLM overhead
        single_discovery_task = Task(
            **self.prompt_manager.build_discovery_task_description('discover_application', prompt_vars), 
            agent=self.discovery_agent, 
            output_file=prompt_vars['SITEMAP_OUTPUT_FILE']
        )

        self.tasks = [single_discovery_task]

    async def crew(self) -> Crew:
        if self.base_url:
            tool_map = self.get_tool_map(self.tools)
            navigate_tool = tool_map.get('browser_navigate')
            if navigate_tool:
                navigate_tool._run(url=self.base_url)
                await self.wait_for_page_load(tool_map)

        instructions = self.prompt_manager.get_core_component('safety_rules').get('content', {}).get('mandatory_instructions', '')
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            tools=self.tools,
            process=Process.sequential,
            verbose=False,  # Reduce verbose output to minimize LLM calls
            telemetry=False,
            max_iter=300,  # Increased to handle all 34+ pages
            output_log_file=self.getTaskOutFilePath('crew_output.log'),
            output_dir=f'backend/fs_files/{self.test_run_id}',
            step_callback=lambda step: None,  # Disable step callbacks to reduce overhead
            manager_llm=self.azure_llm
        )

    async def wait_for_page_load(self, tool_map, timeout_sec=30):
        wait_tool = tool_map.get('browser_wait_for')
        if wait_tool:
            for cond in [{"textGone": "Loading"}, {"text": "Sign in"}, {"text": "Continue"}]:
                try:
                    wait_tool._run(time=timeout_sec, **cond)
                    return
                except Exception:
                    continue

    def get_tool_map(self, tools):
        return {getattr(tool, 'name', tool.__class__.__name__): tool for tool in tools or []}

    def getTaskOutFilePath(self, filename: str):
        return f'backend/fs_files/{self.test_run_id}/{filename}'

    def set_base_url(self, base_url: str):
        self.base_url = base_url
        self.create_agents()
        self.create_tasks()

    def set_socket_manager(self, socket_manager):
        self.socket_manager = socket_manager
        if socket_manager:
            ws_handler = WebSocketLogHandler(socket_manager, source="CrewAI")
            ws_handler.setLevel(logging.INFO)
            ws_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
            if not any(isinstance(h, WebSocketLogHandler) for h in logging.getLogger().handlers):
                logging.getLogger().addHandler(ws_handler)

    def get_cost(self):
        costs = 0.150 * (self.crew.usage_metrics.prompt_tokens + self.crew.usage_metrics.completion_tokens) / 1_000_000
        print(f"Total costs: ${costs:.4f}")

        # Convert UsageMetrics instance to a DataFrame
        try:
            df_usage_metrics = pd.DataFrame([self.crew.usage_metrics.dict()])
            return df_usage_metrics
        except Exception:
            # Return the raw usage metrics if pandas is not available or fails
            return self.crew.usage_metrics.dict()
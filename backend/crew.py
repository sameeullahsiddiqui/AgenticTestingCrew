import asyncio
import os
from dotenv import load_dotenv
from typing import List
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import MCPServerAdapter
from crewai_tools import FileWriterTool
from crewai_tools import FileReadTool
from mcp import StdioServerParameters

from backend.helpers.socket_manager import SocketManager
from backend.helpers.socket_log_handler import WebSocketLogHandler

import logging

# Setup logger
log_dir = "backend/fs_files/logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/testing_crew.log"),
        logging.StreamHandler()
    ]
)

@CrewBase
class TestingCrew():
    agents: List
    tasks: List
    socket_manager: SocketManager = None
    agents_to_run: List[str]
    force: bool
    test_run_id: str

    def __init__(self, azure_llm, tools, test_run_id):
        self.azure_llm = azure_llm
        self.tools = tools
        self.test_run_id = test_run_id

        super().__init__()

    @classmethod
    async def create(cls, test_run_id):
        load_dotenv()
        
        azure_llm = LLM(
            model="azure/gpt-4.1",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            BASE_URL=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )

        tools = [FileWriterTool(), FileReadTool()]
        
        self_temp = cls.__new__(cls)  # don't call __init__ yet
        mcp_tools = await self_temp._setup_mcp_servers()
        tools.extend(mcp_tools)

        return cls(azure_llm=azure_llm, tools=tools, test_run_id=test_run_id)

    def set_test_run_id(self, test_run_id: str):
        self.test_run_id = test_run_id

    def set_socket_manager(self, socket_manager):
        self.socket_manager = socket_manager
        
        if self.socket_manager:
            ws_handler = WebSocketLogHandler(self.socket_manager, source="CrewAI")
            ws_handler.setLevel(logging.INFO)
            ws_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
            
            if not any(isinstance(h, WebSocketLogHandler) for h in logging.getLogger().handlers):
                logging.getLogger().addHandler(ws_handler)


    def getTaskOutFilePath(self, filename: str):
        return f'backend/fs_files/{self.test_run_id}/{filename}' if hasattr(self, 'test_run_id') else f'backend/fs_files/{filename}'

    
    async def emit_log(self, message: str):
        # print(message)
        if self.socket_manager:
            await self.socket_manager.broadcast({
                "type": "log",
                "source": self.__class__.__name__,
                "message": message
            })

    async def _setup_mcp_servers(self):
        try:
            mcp_params = [
                StdioServerParameters(
                    command="npx",
                    args=["-y", "@executeautomation/playwright-mcp-server"],
                    env=os.environ.copy()
                )
            ]
            tools = MCPServerAdapter(mcp_params).tools
            await self.emit_log("MCP server setup complete.")
            return tools
        except Exception as e:
            await self.emit_log(f"MCP setup failed: {e}. Continuing without tools.")
            return []        
    
    @agent
    def pm(self) -> Agent:
        return Agent(
            config=self.agents_config['pm'], # type: ignore[index]
            llm = self.azure_llm,            
            instructionsfile='agent_instructions/pm_instructions.txt',
            verbose=True        
            )

    @agent
    def discovery(self) -> Agent:
        return Agent(
            config=self.agents_config['discovery'], # type: ignore[index]
            llm = self.azure_llm,
            tools= self.tools,
            instructionsfile='agent_instructions/discovery_instructions.txt',
            verbose=True
            )

    @agent
    def validator(self) -> Agent:
        return Agent(
            config=self.agents_config['validator'],  # merged reviewer + validation role
            llm=self.azure_llm,
            tools= self.tools,
            instructionsfile='agent_instructions/validator_instructions.txt',
            verbose=True
        )
    
    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'], # type: ignore[index]
            llm = self.azure_llm,
            tools= self.tools,
            verbose=True
            )

    @agent
    def planning(self) -> Agent:
        return Agent(
            config=self.agents_config['planning'], # type: ignore[index]
            llm = self.azure_llm,
            tools= self.tools,
            verbose=True
            )

    @agent
    def execution(self) -> Agent:
        return Agent(
            config=self.agents_config['execution'], # type: ignore[index]
            llm = self.azure_llm,
            tools= self.tools,
            verbose=True
            )

    @agent
    def reporting(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting'], # type: ignore[index]
            llm = self.azure_llm,
            tools= self.tools,
            verbose=True
            )


    @task
    def discover_application(self) -> Task:
        return Task(
            config=self.tasks_config['discover_application'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('01_Application_Analysis.md')
        )

    @task
    def build_site_map(self) -> Task:
        return Task(
            config=self.tasks_config['build_site_map'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('build_site_map.md')
        )

    @task
    def validate_discovery(self) -> Task:
        return Task(
            config=self.tasks_config['validate_discovery'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('validate_discovery.md')
        )

    @task
    def review_discovery(self) -> Task:
        return Task(
            config=self.tasks_config['review_discovery'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('review_discovery.md')
        )

    @task
    def generate_test_plan(self) -> Task:
        return Task(
            config=self.tasks_config['generate_test_plan'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('02_Test_Plan.md')
        )
    
    @task
    def execute_tests(self) -> Task:
        return Task(
            config=self.tasks_config['execute_tests'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('03_Execute_Test.md')
        )

    @task
    def generate_test_report(self) -> Task:
        return Task(
            config=self.tasks_config['generate_test_report'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('04_Test_Report_Summry.md')
        )

    @task
    def final_approval(self) -> Task:
        return Task(
            config=self.tasks_config['final_approval'], # type: ignore[index]
            output_file=self.getTaskOutFilePath('05_Test_Execution_Status.md')
        )

    # @task
    # def approve_final_pipeline(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['approve_final_pipeline'], # type: ignore[index]
    #         output_file=self.getTaskOutFilePath('approve_final_pipeline.md')
    #     )


    @crew
    def crew(self, agents_to_run: list[str] = None) -> Crew:
        logging.info("Initializing crew...")

        if agents_to_run:
            filtered_agents = [agent for agent in self.agents if agent.role in agents_to_run]
            agent_names = {agent.role for agent in filtered_agents}
            filtered_tasks = [task for task in self.tasks if task.agent.role in agent_names]
            logging.info(f"Filtered agents: {[a.role for a in filtered_agents]}")
            logging.info(f"Filtered tasks: {[t.description for t in filtered_tasks]}")
            if len(filtered_agents) ==0:
                raise 'No agent to run'
        else:
            filtered_agents = self.agents
            filtered_tasks = self.tasks

        logging.info("Agents and tasks loaded.")

        return Crew(
            agents=filtered_agents,
            tasks=filtered_tasks,
            tools=self.tools,
            process=Process.sequential,
            verbose=True
        )
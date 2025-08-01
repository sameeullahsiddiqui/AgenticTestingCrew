import asyncio
import os
import sys
from typing import List
from datetime import datetime

from backend.crew import TestingCrew
from backend.helpers.socket_manager import SocketManager
from backend.helpers.stdout_redirector import StdoutCapture

class CrewOrchestrator:
    def __init__(self, socket_manager=None, test_run_id= f"run_{datetime.now():%Y%m%d_%H%M%S}"):        
        self.socket_manager = socket_manager
        self.test_run_id = test_run_id

    async def run_pipeline(self,agents_to_run: List[str] , inputs:dict[str, any], force:bool):
        """
        Inputs = {
                    "base_url": "https://www.saucedemo.com/",
                    "instructions": "Focus on shopping cart flows",
                    "force": false,
                    "headless": false,
                    "agents_to_run": ["discover_application"],
                    "test_run_id":"run_20250727_084413"
                }
        """

        try:
            os.environ["TEST_RUN_ID"] = self.test_run_id
            base_dir = os.path.join(os.getcwd(), "backend", "fs_files")
            samples_dir = os.path.join(base_dir, self.test_run_id)

            if inputs['BASE_URL'] == '':
                await self.emit_log(f"Please provide testing url.")
                raise

            # await self.emit_log("Starting CrewAI Pipeline")
            # await self.emit_log(f"Working directory: {base_dir}")
            # await self.emit_log(f"Samples directory: {samples_dir}")


            sys.stdout = StdoutCapture(self.socket_manager, source="CrewAI")
            
            import json

            formatted_inputs = "\n".join([f"{key}: {value}" for key, value in inputs.items()])
            await self.emit_log(f"🚀 Starting pipeline with parameters:")
            await self.emit_log(f"{formatted_inputs}")


            crew_instance = await TestingCrew.create(self.test_run_id)

            crew_instance.set_test_run_id(self.test_run_id)
            crew_instance.set_socket_manager(self.socket_manager)
            crew_instance.agents_to_run = agents_to_run
            crew_instance.force = force


            await self.emit_log("Crew setup complete, beginning execution...")

            os.makedirs(samples_dir, exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "logs"), exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "screenshots"), exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "evidence"), exist_ok=True)

            inputs['SAMPLE_DIR'] = samples_dir

            inputs = self.update_instructions_with_pre_steps(inputs)
            result = crew_instance.crew().kickoff(inputs= inputs)

            await self.emit_log("\n\n=== FINAL REPORT ===\n")
            await self.emit_log(result.raw)
            await self.emit_log("\nReport saved to output/report.md")
            await self.emit_log("Crew execution finished successfully.")

            sys.stdout = sys.__stdout__

            return result
            

        except Exception as e:
            sys.stdout = sys.__stdout__  # Ensure we restore it on error
            await self.emit_log(f"Pipeline error: {e}")
            raise

    def update_instructions_with_pre_steps(self, inputs, file_path="agent_instructions/mandatory_pre_steps.txt"):
        try:
            with open(file_path, "r") as file:
                pre_steps = file.read()
            
            pre_steps = pre_steps.replace("{BASE_URL}", inputs["base_url"])
            inputs["instructions"] += "\n\n" + pre_steps
            return inputs
        
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return inputs
        
        
    async def emit_log(self, message: str):
        # print(message)
        if self.socket_manager:
            await self.socket_manager.broadcast({
                "type": "log",
                "source": self.__class__.__name__,
                "message": message
            })


if __name__ == "__main__":

    orchestrator = CrewOrchestrator()
    asyncio.run(orchestrator.run_pipeline())

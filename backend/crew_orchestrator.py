import asyncio
import os
import sys
import warnings
from typing import List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from backend.crew_test_explorer import ExplorationCrew
from backend.crew_test_planner import TestPlanningCrew
from backend.crew_test_executor import TestExecutionCrew
from backend.crew_test_reporter import TestReportingCrew
from backend.helpers.socket_manager import SocketManager
from backend.helpers.stdout_redirector import StdoutCapture

class CrewOrchestrator:
    def __init__(self, socket_manager=None, test_run_id= f"run_{datetime.now():%Y%m%d_%H%M%S}"):        
        self.socket_manager = socket_manager
        self.test_run_id = test_run_id

    async def run_pipeline(self, inputs: dict[str, any], force: bool):
        """
        Multi-Phase Testing Pipeline:
        Phase 1: Exploration - Discovery and mapping
        Phase 2: Planning - Test strategy and scenarios  
        Phase 3: Execution - Script generation and test execution
        Phase 4: Reporting - Analysis and stakeholder communication
        
        Inputs = {
            "BASE_URL": "https://www.saucedemo.com/",
            "INSTRUCTIONS": "Focus on shopping cart flows",
            "FORCE": false,
            "HEADLESS": false,
            "TEST_RUN_ID": "run_20250727_084413",
            "PHASES": ["exploration", "planning", "execution", "reporting"]  # New: specify which phases to run
        }
        """

        try:
            os.environ["TEST_RUN_ID"] = self.test_run_id
            base_dir = os.path.join(os.getcwd(), "backend", "fs_files")
            samples_dir = os.path.join(base_dir, self.test_run_id)

            if inputs['BASE_URL'] == '':
                await self.emit_log(f"Please provide testing url.")
                return

            sys.stdout = StdoutCapture(self.socket_manager, source="CrewAI")
            
            formatted_inputs = "\n".join([f"{key}: {value}" for key, value in inputs.items()])
            await self.emit_log(f"🚀 Starting multi-phase testing pipeline:")
            await self.emit_log(f"{formatted_inputs}")

            # Create output directories
            os.makedirs(samples_dir, exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "logs"), exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "screenshots"), exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "evidence"), exist_ok=True)
            os.makedirs(os.path.join(samples_dir, "test_scripts"), exist_ok=True)

            inputs['SAMPLE_DIR'] = samples_dir
            inputs = self.update_instructions_with_pre_steps(inputs)

            # Determine which phases to run
            phases_to_run = inputs.get('PHASES', ['exploration', 'planning', 'execution', 'reporting'])
            await self.emit_log(f"📋 Phases to execute: {phases_to_run}")

            pipeline_results = {}

            # PHASE 1: EXPLORATION
            if 'exploration' in phases_to_run:
                await self.emit_log("\n" + "="*60)
                await self.emit_log("🔍 PHASE 1: APPLICATION EXPLORATION")
                await self.emit_log("="*60)
                
                self.exploration_crew_instance = await ExplorationCrew.create(self.test_run_id, inputs["BASE_URL"])
                self.exploration_crew_instance.set_socket_manager(self.socket_manager)
                self.exploration_crew_instance.force = force

                crew_instance = await self.exploration_crew_instance.crew()
                exploration_result = crew_instance.kickoff(inputs=inputs)
                
                pipeline_results['exploration'] = exploration_result
                await self.emit_log("✅ Phase 1: Exploration completed successfully")
                
                # Check if exploration was successful before proceeding
                if not self.validate_phase_output('exploration', samples_dir):
                    await self.emit_log("❌ Exploration phase validation failed. Stopping pipeline.")
                    return pipeline_results

            # PHASE 2: PLANNING
            if 'planning' in phases_to_run:
                await self.emit_log("\n" + "="*60)
                await self.emit_log("📋 PHASE 2: TEST PLANNING")
                await self.emit_log("="*60)
                
                planning_crew_instance = await TestPlanningCrew.create(self.test_run_id, inputs["BASE_URL"])
                planning_crew_instance.set_socket_manager(self.socket_manager)
                planning_crew_instance.force = force

                planning_crew = await planning_crew_instance.crew(inputs["BASE_URL"])
                planning_result = planning_crew.kickoff(inputs=inputs)
                
                pipeline_results['planning'] = planning_result
                await self.emit_log("✅ Phase 2: Planning completed successfully")
                
                # Check if planning was successful before proceeding
                if not self.validate_phase_output('planning', samples_dir):
                    await self.emit_log("❌ Planning phase validation failed. Stopping pipeline.")
                    return pipeline_results

            # PHASE 3: EXECUTION
            if 'execution' in phases_to_run:
                await self.emit_log("\n" + "="*60)
                await self.emit_log("⚡ PHASE 3: TEST EXECUTION")
                await self.emit_log("="*60)
                
                execution_crew_instance = await TestExecutionCrew.create(self.test_run_id, inputs["BASE_URL"])
                execution_crew_instance.set_socket_manager(self.socket_manager)
                execution_crew_instance.force = force

                execution_crew = await execution_crew_instance.crew(inputs["BASE_URL"])
                execution_result = execution_crew.kickoff(inputs=inputs)
                
                pipeline_results['execution'] = execution_result
                await self.emit_log("✅ Phase 3: Execution completed successfully")
                
                # Check if execution was successful before proceeding
                if not self.validate_phase_output('execution', samples_dir):
                    await self.emit_log("❌ Execution phase validation failed. Stopping pipeline.")
                    return pipeline_results

            # PHASE 4: REPORTING
            if 'reporting' in phases_to_run:
                await self.emit_log("\n" + "="*60)
                await self.emit_log("📊 PHASE 4: REPORTING & ANALYSIS")
                await self.emit_log("="*60)
                
                reporting_crew_instance = await TestReportingCrew.create(self.test_run_id, inputs["BASE_URL"])
                reporting_crew_instance.set_socket_manager(self.socket_manager)
                reporting_crew_instance.force = force

                reporting_crew = await reporting_crew_instance.crew(inputs["BASE_URL"])
                reporting_result = reporting_crew.kickoff(inputs=inputs)
                
                pipeline_results['reporting'] = reporting_result
                await self.emit_log("✅ Phase 4: Reporting completed successfully")

            # PIPELINE COMPLETION
            await self.emit_log("\n" + "="*60)
            await self.emit_log("🎉 MULTI-PHASE TESTING PIPELINE COMPLETED")
            await self.emit_log("="*60)
            
            await self.emit_log(f"📁 All outputs saved to: {samples_dir}")
            await self.emit_log(f"🔗 Application tested: {inputs['BASE_URL']}")
            await self.emit_log(f"📋 Phases completed: {list(pipeline_results.keys())}")
            
            if 'reporting' in pipeline_results:
                await self.emit_log("\n📊 FINAL REPORTING SUMMARY:")
                report_summary = str(pipeline_results['reporting'].raw)[:500] + "..." if len(str(pipeline_results['reporting'].raw)) > 500 else str(pipeline_results['reporting'].raw)
                await self.emit_log(report_summary)

            sys.stdout = sys.__stdout__
            return pipeline_results

        except Exception as e:
            sys.stdout = sys.__stdout__
            await self.emit_log(f"Pipeline error: {e}")
            raise

    def validate_phase_output(self, phase: str, samples_dir: str) -> bool:
        """
        Validate that a phase has produced the expected outputs
        Returns True if validation passes, False otherwise
        """
        try:
            validation_rules = {
                'exploration': {
                    'files': ['discovery_summary.json', 'site_map.json'],
                    'description': 'Site discovery and mapping outputs'
                },
                'planning': {
                    'files': ['test_strategy.json', 'test_scenarios.json'],
                    'description': 'Test planning and scenario outputs'
                },
                'execution': {
                    'files': ['test_results.json', 'execution_log.txt'],
                    'directories': ['test_scripts'],
                    'description': 'Test execution and script outputs'
                },
                'reporting': {
                    'files': ['final_report.json', 'executive_summary.txt'],
                    'description': 'Final reporting and analysis outputs'
                }
            }
            
            if phase not in validation_rules:
                print(f"⚠️ No validation rules for phase: {phase}")
                return True  # Allow unknown phases to continue
            
            rules = validation_rules[phase]
            missing_files = []
            
            # Check for required files
            if 'files' in rules:
                for required_file in rules['files']:
                    file_path = os.path.join(samples_dir, required_file)
                    if not os.path.exists(file_path):
                        missing_files.append(required_file)
            
            # Check for required directories
            if 'directories' in rules:
                for required_dir in rules['directories']:
                    dir_path = os.path.join(samples_dir, required_dir)
                    if not os.path.exists(dir_path):
                        missing_files.append(f"{required_dir}/ (directory)")
            
            if missing_files:
                print(f"❌ Phase {phase} validation failed - Missing: {', '.join(missing_files)}")
                print(f"   Expected {rules['description']}")
                return False
            else:
                print(f"✅ Phase {phase} validation passed - {rules['description']}")
                return True
                
        except Exception as e:
            print(f"⚠️ Phase {phase} validation error: {e}")
            return True  # Don't block pipeline on validation errors

    def update_instructions_with_pre_steps(self, inputs, file_path="backend/agent_instructions/mandatory_pre_steps.txt"):
        """
        Update instructions with pre-steps. 
        This method is kept for backward compatibility but will use new prompt system when available.
        """
        try:
            # Try to use new prompt system first
            if hasattr(self, 'exploration_crew_instance') and hasattr(self.exploration_crew_instance, 'prompt_manager'):
                safety_rules = self.exploration_crew_instance.prompt_manager.get_core_component('safety_rules')
                pre_steps = safety_rules.get('content', {}).get('mandatory_instructions', '')
                print("✅ Using pre-steps from new prompt system")
            else:
                # Fallback to legacy file-based approach
                with open(file_path, "r") as file:
                    pre_steps = file.read()
                print("✅ Using pre-steps from legacy file system")
     
            pre_steps = pre_steps.replace("{BASE_URL}", inputs["BASE_URL"])
            inputs["INSTRUCTIONS"] += "\n\n" + pre_steps
            return inputs
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return inputs
        except Exception as e:
            print(f"Error loading pre-steps: {e}")
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

    # Get demo application URL from environment variable
    SSO_LOGIN_URL = os.getenv('DEMO_SSO_LOGIN_URL', 'https://www.saucedemo.com/')
    
    orchestrator = CrewOrchestrator()
    
    inputs = {
        "BASE_URL": SSO_LOGIN_URL,
        "INSTRUCTIONS": "",
        "HEADLESS": "False",
        "FORCE": False,
        "TARGET_PAGES": 100,
        "TARGET_PAGE_COUNT": 100,
        "TEST_RUN_ID": "run_20250820_ecommerce",
        "OUTPUT_DIR": "backend/fs_files/run_20250820_ecommerce",
        "PHASES": ["exploration"]  
        # "PHASES": ["exploration", "planning", "execution", "reporting"]  
    }
    
    force = False

    print("🚀 Starting Multi-Phase Testing Pipeline")
    print(f"📋 Phases to execute: {inputs['PHASES']}")
    print(f"🔗 Target application: {inputs['BASE_URL']}")
    
    asyncio.run(orchestrator.run_pipeline(inputs, force))

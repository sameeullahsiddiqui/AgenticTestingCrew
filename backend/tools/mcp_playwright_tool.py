from crewai.tools import BaseTool
from typing import Type, Optional, Union
from pydantic import BaseModel, Field
import subprocess
import json
import os
import tempfile
import time


class PlaywrightNavigateInput(BaseModel):
    """Input schema for Playwright Navigate tool."""
    url: str = Field(..., description="URL to navigate to")
    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30000, description="Navigation timeout in milliseconds")

class PlaywrightScreenshotInput(BaseModel):
    """Input schema for Playwright Screenshot tool."""
    name: str = Field(..., description="Name for the screenshot file")
    full_page: bool = Field(default=False, description="Take full page screenshot")
    save_path: str = Field(default="screenshots", description="Directory to save screenshot")

class PlaywrightClickInput(BaseModel):
    """Input schema for Playwright Click tool."""
    selector: str = Field(..., description="CSS selector for the element to click")

class PlaywrightFillInput(BaseModel):
    """Input schema for Playwright Fill tool."""
    selector: str = Field(..., description="CSS selector for the input field")
    value: str = Field(..., description="Value to fill in the input field")

class PlaywrightGetTextInput(BaseModel):
    """Input schema for Playwright Get Text tool."""
    selector: str = Field(default="body", description="CSS selector to get text from (default: entire page)")

class MyCustomTool(BaseTool):
    """A custom Playwright tool that works directly with the MCP server via subprocess."""
    
    name: str = "Playwright Browser Tool"
    description: str = (
        "A comprehensive Playwright tool for browser automation. Can navigate to URLs, take screenshots, "
        "click elements, fill forms, and extract text from web pages. This tool communicates directly "
        "with the Playwright MCP server to perform browser automation tasks."
    )
    args_schema: Type[BaseModel] = PlaywrightNavigateInput

    def _run_mcp_command(self, method: str, params: dict = None) -> dict:
        """Run an MCP command and return the result."""
        try:
            command_data = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),  # Use timestamp as ID
                "method": method
            }
            if params:
                command_data["params"] = params
            
            # Convert to JSON string and escape for PowerShell
            json_command = json.dumps(command_data, separators=(',', ':'))
            
            # Use PowerShell with proper escaping
            cmd = f'echo \'{json_command}\' | npx @playwright/mcp'
            
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse the JSON response
                response = json.loads(result.stdout.strip())
                return response
            else:
                return {
                    "error": f"Command failed: {result.stderr or 'No output'}",
                    "returncode": result.returncode,
                    "stdout": result.stdout
                }
                    
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 30 seconds"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {str(e)}", "raw_output": result.stdout if 'result' in locals() else 'No output'}
        except Exception as e:
            return {"error": f"Failed to execute MCP command: {str(e)}"}

    def _run(self, **kwargs) -> str:
        """Main execution method that handles different Playwright operations based on provided arguments."""
        
        # Determine which operation to perform based on the arguments provided
        if 'url' in kwargs:
            return self._navigate(kwargs['url'], kwargs.get('headless', True), kwargs.get('timeout', 30000))
        elif 'name' in kwargs and 'selector' not in kwargs:
            return self._screenshot(kwargs['name'], kwargs.get('full_page', False), kwargs.get('save_path', 'screenshots'))
        elif 'selector' in kwargs and 'value' in kwargs:
            return self._fill(kwargs['selector'], kwargs['value'])
        elif 'selector' in kwargs and 'value' not in kwargs:
            if kwargs.get('action') == 'click':
                return self._click(kwargs['selector'])
            else:
                return self._get_text(kwargs['selector'])
        else:
            return "Error: Invalid arguments provided. Use url for navigation, name for screenshots, selector+value for filling, or selector for clicking/getting text."

    def _navigate(self, url: str, headless: bool = True, timeout: int = 30000) -> str:
        """Navigate to a URL."""
        params = {
            "url": url,
            "headless": headless,
            "timeout": timeout
        }
        
        result = self._run_mcp_command("tools/call", {
            "name": "playwright_navigate",
            "arguments": params
        })
        
        if "error" in result:
            return f"Navigation failed: {result['error']}"
        else:
            return f"Successfully navigated to {url}"

    def _screenshot(self, name: str, full_page: bool = False, save_path: str = "screenshots") -> str:
        """Take a screenshot."""
        # Ensure directory exists
        os.makedirs(save_path, exist_ok=True)
        
        params = {
            "name": name,
            "fullPage": full_page,
            "savePng": True,
            "downloadsDir": os.path.abspath(save_path)
        }
        
        result = self._run_mcp_command("tools/call", {
            "name": "playwright_screenshot",
            "arguments": params
        })
        
        if "error" in result:
            return f"Screenshot failed: {result['error']}"
        else:
            return f"Screenshot saved as {name} in {save_path}/"

    def _click(self, selector: str) -> str:
        """Click an element."""
        result = self._run_mcp_command("tools/call", {
            "name": "playwright_click",
            "arguments": {"selector": selector}
        })
        
        if "error" in result:
            return f"Click failed: {result['error']}"
        else:
            return f"Successfully clicked element: {selector}"

    def _fill(self, selector: str, value: str) -> str:
        """Fill an input field."""
        result = self._run_mcp_command("tools/call", {
            "name": "playwright_fill",
            "arguments": {"selector": selector, "value": value}
        })
        
        if "error" in result:
            return f"Fill failed: {result['error']}"
        else:
            return f"Successfully filled {selector} with: {value}"

    def _get_text(self, selector: str = "body") -> str:
        """Get visible text from page or element."""
        if selector == "body":
            result = self._run_mcp_command("tools/call", {
                "name": "playwright_get_visible_text",
                "arguments": {}
            })
        else:
            result = self._run_mcp_command("tools/call", {
                "name": "playwright_get_visible_html",
                "arguments": {"selector": selector, "maxLength": 5000}
            })
        
        if "error" in result:
            return f"Get text failed: {result['error']}"
        else:
            content = result.get('result', {}).get('content', 'No content returned')
            return f"Text content: {content[:1000]}..." if len(str(content)) > 1000 else f"Text content: {content}"


# Additional specialized tools for specific operations
class PlaywrightNavigateTool(MyCustomTool):
    name: str = "Playwright Navigate"
    description: str = "Navigate to a specific URL using Playwright browser automation"
    args_schema: Type[BaseModel] = PlaywrightNavigateInput

class PlaywrightScreenshotTool(MyCustomTool):
    name: str = "Playwright Screenshot"
    description: str = "Take a screenshot of the current page or element"
    args_schema: Type[BaseModel] = PlaywrightScreenshotInput

class PlaywrightClickTool(MyCustomTool):
    name: str = "Playwright Click"
    description: str = "Click on an element using CSS selector"
    args_schema: Type[BaseModel] = PlaywrightClickInput

class PlaywrightFillTool(MyCustomTool):
    name: str = "Playwright Fill"
    description: str = "Fill an input field with text"
    args_schema: Type[BaseModel] = PlaywrightFillInput

class PlaywrightGetTextTool(MyCustomTool):
    name: str = "Playwright Get Text"
    description: str = "Extract visible text from page or specific element"
    args_schema: Type[BaseModel] = PlaywrightGetTextInput

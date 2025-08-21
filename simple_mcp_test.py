import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import os
import traceback
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

SSO_LOGIN_URL = ("www.google.com")

async def setup_mcp_servers():
    env = os.environ.copy()
    env['BROWSER'] = 'msedge'
    env['PLAYWRIGHT_BROWSER'] = 'msedge'
    mcp_params = [StdioServerParameters(command="npx", args=["-y", "@playwright/mcp"], env=env)]
    return MCPServerAdapter(mcp_params).tools

def get_tool_map(tools):
    return {getattr(tool, 'name', tool.__class__.__name__): tool for tool in tools or []}

async def wait_for_page_load(tool_map, timeout_sec=30):
    wait_tool = tool_map.get('browser_wait_for')
    if wait_tool:
        for cond in [{"textGone": "Loading"}, {"text": "Sign in"}, {"text": "Continue"}]:
            try:
                wait_tool._run(time=timeout_sec, **cond)
                print(f"⏳ Wait condition satisfied: {cond}")
                return
            except Exception:
                continue
    print("⚠️ Page load wait conditions not confirmed; proceeding anyway")

async def wait_until_user_closes_browser(tool_map):
    eval_tool = tool_map.get('browser_evaluate')
    if not eval_tool:
        print("ℹ️ No browser_evaluate tool; press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(2)
    else:
        print("👀 Waiting until you close the browser window…")
        while True:
            try:
                eval_tool._run(function="() => 'ok'")
                await asyncio.sleep(2)
            except Exception:
                print("📪 Browser appears closed. Exiting…")
                break

async def test_browser_navigation(tools):
    tool_map = get_tool_map(tools)
    navigate_tool = tool_map.get('browser_navigate')
    screenshot_tool = tool_map.get('browser_take_screenshot')

    if not navigate_tool:
        print("❌ No browser_navigate tool found")
        return False

    print("🔗 Navigating to SSO login URL…")
    navigate_tool._run(url=SSO_LOGIN_URL)

    await wait_for_page_load(tool_map)

    if screenshot_tool:
        screenshot_tool._run(filename="post_login_homepage.png")
        print("📸 Screenshot saved")

    await wait_until_user_closes_browser(tool_map)
    return True

async def main():
    print("🚀 MCP Test with SSO Login")
    try:
        tools = await setup_mcp_servers()
        print(f"✅ MCP setup completed with {len(tools)} tools")
        success = await test_browser_navigation(tools)
        print(f"\n📊 FINAL RESULT: {'✅ Success' if success else '❌ Failed'}")
        return success
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

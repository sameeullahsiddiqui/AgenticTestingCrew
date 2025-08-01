# 🧪 Agentic Web Test Automation Framework (MCP-Powered)

This repository implements a **multi-agent automation testing system** using OpenAI's Agents SDK and Microsoft’s [MCP Playwright Server](https://www.npmjs.com/package/@executeautomation/playwright-mcp-server).

@mcp@latest --config path/to/config/json

It is designed to:
- Automatically **discover** a complete multi-page web app
- **Plan** test cases (happy + negative + upload scenarios)
- **Execute** them using MCP tools only
- **Review** coverage and **regenerate missing or failed** tests
- Output a **final test report** with logs, screenshots, markdown tables

---

## 🔧 Features

- ✅ Zero custom browser logic — all test interaction via MCP servers only
- 📦 Modular agents: Discovery / Planning / Execution / Reporting / Review
- 🪄 Auto-generates missing file uploads based on page templates
- 🔁 Recovery & retry logic for error-prone steps
- 📂 Full logs and screenshots on failure
- 🧠 Built using OpenAI Agents SDK with Azure OpenAI API
- 🖼️ Frontend dashboard (React UI) supported [WIP]

---

## 🏗️ Folder Structure

```
├── fs_files/                    # File server volume (shared test artifacts)
│   ├── site_map.json            # Discovered site structure
│   ├── automation_plan.md      # Planned test cases
│   ├── automation_plan_results_raw.txt
│   ├── automation_plan_results.md
│   ├── screenshots/            # Captured screenshots
│   └── logs/                   # Output and error logs
│
├── agent_instructions/         # Prompt templates for each agent
│   ├── discovery_instructions.txt
│   ├── planning_instructions.txt
│   ├── execution_instructions.txt
│   ├── reporting_instructions.txt
│   └── review_instructions.txt
│
├── backend/
│   ├── api.py                  # FastAPI backend to expose file listing/downloads
│   ├── scripts/clean_logs.py  # Reset logs/screenshots before test
│   └── tests/                 # Pytest coverage for API + utilities
│
├── orchestrator.py            # Pipeline runner that sequences all agents
├── .env                       # Azure OpenAI API keys and model info
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for MCP servers)
- `npx`, `@modelcontextprotocol/server-filesystem`, `@executeautomation/playwright-mcp-server`
- Azure OpenAI credentials (via `.env`)

### 🏁 Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/agentic-mcp-testing.git
cd agentic-mcp-testing

# Setup Python Backend
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r .\backend\requirements.txt

# Install MCP servers (no code mod required)
npm i @modelcontextprotocol/server-filesystem
npm i @executeautomation/playwright-mcp-server
# npx -y @modelcontextprotocol/server-filesystem
# npx -y @executeautomation/playwright-mcp-server

# Prepare .env
cp .env.example .env  # then fill in AZURE_OPENAI_* values
```

### Setup Node Frontend

```bash
cd frontend
npm install
cd ..

# Start the Backend Server
uvicorn backend.api:app --reload --port 8000

# Start the Frontend
cd frontend
npm run dev
Visit: http://localhost:5173

```

### Run
```bash
python backend/orchestrator.py https://www.saucedemo.com/
```
> All test artifacts will be stored in `backend/fs_files/{test_run_id}/`

---

## 🧠 Agents Overview
| Agent     | Role                                                                 |
|-----------|----------------------------------------------------------------------|
| Discovery | Crawl the app, build site map with pages, links, forms, uploads     |
| Planning  | Generate test plan covering happy, negative, upload cases           |
| Execution | Run tests via MCP, log results, take screenshots, retry on failure  |
| Review    | Identify missing or failed tests, regenerate partial plan            |
| Reporting | Summarize test results and generate final markdown report           |

---

## 🛠️ Dev Notes

- Re-run cleanup before new session:
  ```bash
  python backend/scripts/clean_logs.py
  ```

- React frontend support (WIP):
  - URL input, live console logs, downloadable artifacts
  - Hosted via Vercel or local dev server

---

## 🖥️ Running the Full Application

### 1. Install Prerequisites
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

npm install -g @modelcontextprotocol/server-filesystem @executeautomation/playwright-mcp-server
```

### 2. Setup Environment
Create `.env` in root:
```env
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://your-endpoint.openai.azure.com/
OPENAI_API_VERSION=2023-07-01-preview
OPENAI_DEPLOYMENT_MODEL=gpt-4
```

### 3. Start the Backend
```bash
uvicorn backend.api:app --reload --port 8000
```

### 4. Start the Frontend
```bash
cd test-runner=app
npm install
npm run build
npm run run
```

Add proxy in `vite.config.js`:
```js
server: {
  proxy: {
    "/run": "http://localhost:8000",
    "/list-files": "http://localhost:8000",
    "/download": "http://localhost:8000",
  },
},
```

### 5. Use the UI
- Visit: `http://localhost:5173`
- Enter app URL and click **Run Test**
- View results, logs, and download artifacts

---

## 📄 License
MIT

---

## 🙌 Acknowledgements
- [OpenAI Agents SDK](https://platform.openai.com/docs/assistants)
- [ExecuteAutomation MCP Server](https://www.npmjs.com/package/@executeautomation/playwright-mcp-server)
- [Model Context Protocol](https://github.com/modelcontextprotocol)

---


poetry init
poetry run uvicorn backend.main:app --reload
pip install pyinstaller
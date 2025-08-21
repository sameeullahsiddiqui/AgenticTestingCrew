# Environment Setup Guide

## 🚀 Quick Setup

### 1. Copy Template Files
```bash
# Copy the template to create your .env file
cp backend/.env.template backend/.env
```

### 2. Configure Azure OpenAI (Required)
Edit `backend/.env` and update these essential values:

```bash
# Get these from your Azure Portal > Azure OpenAI Service
AZURE_API_KEY=your_actual_api_key_from_azure_portal
AZURE_API_BASE=https://your-resource-name.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=your_gpt4_deployment_name
```

### 3. Configure Testing URL (Required)
```bash
# Replace with your actual application URL
DEMO_SSO_LOGIN_URL=https://www.saucedemo.com/
TARGET_APPLICATION_URL=https://your-actual-application-url.com
```

### 4. Verify Setup
```bash
# Test your configuration
python backend/main.py
```

## 📋 Complete Configuration Options

### Azure OpenAI Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_API_KEY` | Your Azure OpenAI API key | `abc123...` |
| `AZURE_API_BASE` | Your Azure OpenAI endpoint | `https://myai.openai.azure.com` |
| `AZURE_API_VERSION` | API version | `2024-12-01-preview` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | GPT deployment name | `gpt-4` |

### Application URLs
| Variable | Description | Example |
|----------|-------------|---------|
| `DEMO_SSO_LOGIN_URL` | Primary demo testing URL | `https://www.saucedemo.com/` |
| `TARGET_APPLICATION_URL` | Your application URL | `https://your-app.com/login` |
| `SAMPLE_ECOMMERCE_URL` | Demo e-commerce site | `https://automationexercise.com/` |
| `TEST_URL_DEMO` | Demo testing site | `https://demo.testim.io/` |

### CrewAI Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `CREWAI_ENHANCED_MODE` | Enable enhanced trained model | `true` |
| `CREWAI_MODEL_VERSION` | Model version identifier | `crewai-discovery-specialist-v1.0` |
| `CREWAI_DISABLE_TELEMETRY` | Disable data collection | `true` |

### Browser Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `BROWSER` | Browser to use | `msedge` |
| `PLAYWRIGHT_BROWSER` | Playwright browser | `msedge` |
| `HEADLESS` | Run in headless mode | `false` |

## 🔒 Security Best Practices

### 1. Never Commit Secrets
```bash
# Add to .gitignore (already included)
backend/.env
.env
*.env
!.env.template
```

### 2. Use Different Environments
```bash
# Development
backend/.env

# Production  
backend/.env.production

# Testing
backend/.env.test
```

### 3. Validate Configuration
```bash
# Check for missing variables
python -c "
```bash
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

required = ['AZURE_API_KEY', 'AZURE_API_BASE', 'DEMO_SSO_LOGIN_URL']
missing = [var for var in required if not os.getenv(var)]

if missing:
    print(f'❌ Missing required variables: {missing}')
else:
    print('✅ All required variables configured')
"
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Azure OpenAI Authentication Failed
```bash
# Check your API key and endpoint are working correctly
curl -H "api-key: YOUR_API_KEY" \
     https://your-resource.openai.azure.com/openai/deployments/your-deployment/completions?api-version=2024-12-01-preview
```

#### 2. Environment Variables Not Loading
```bash
# Verify file location and content
ls -la backend/.env
cat backend/.env | grep -v "^#" | grep -v "^$"
```

#### 3. CrewAI Enhanced Mode Not Working
```bash
# Check enhanced mode status
python -c "
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
print('Enhanced Mode:', os.getenv('CREWAI_ENHANCED_MODE'))
print('Model Version:', os.getenv('CREWAI_MODEL_VERSION'))
"
```

## 📈 Environment-Specific Configurations

### Development
```bash
# backend/.env.development
LOG_LEVEL=DEBUG
DEBUG_MODE=true
HEADLESS=false
MAX_WORKERS=2
```

### Production
```bash
# backend/.env.production
LOG_LEVEL=WARNING
DEBUG_MODE=false
HEADLESS=true
MAX_WORKERS=8
TIMEOUT_SECONDS=60
```

### Testing
```bash
# backend/.env.test
DEMO_SSO_LOGIN_URL=https://demo.testim.io/
TARGET_APPLICATION_URL=https://test-environment.com
LOG_LEVEL=INFO
HEADLESS=true
```

## 🎯 Getting Help

### 1. Check Configuration
```bash
python training/validate_deployment.py
```

### 2. Test Enhanced Model
```bash
python training/test_enhanced_orchestrator.py
```

### 3. Verify Environment
```bash
python -c "
from backend.crew_orchestrator import CrewOrchestrator
print('✅ Configuration loaded successfully')
"
```

---
*For more help, check the project documentation or create an issue.*

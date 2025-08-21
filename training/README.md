# CrewAI Training Solution

This directory contains a comprehensive training solution for improving CrewAI agent performance in web application discovery and testing.

## Training Components

### 1. **Datasets** (`/datasets/`)
- **discovery_training_data.jsonl** - Browser automation training examples
- **agent_response_patterns.json** - Expected agent behavior patterns
- **tool_usage_examples.json** - Correct tool usage sequences
- **error_correction_data.json** - Common mistakes and corrections

### 2. **Models** (`/models/`)
- **custom_crew_model.py** - Custom model wrapper for CrewAI
- **fine_tuning_config.yaml** - Training hyperparameters
- **model_adapter.py** - Adapter for different LLM providers

### 3. **Evaluation** (`/evaluation/`)
- **performance_metrics.py** - Custom evaluation metrics
- **benchmark_tests.py** - Standardized performance tests
- **quality_assessor.py** - Output quality evaluation

### 4. **Training Pipeline**
- **train_crew.py** - Main training script
- **data_generator.py** - Synthetic training data generation
- **evaluation_runner.py** - Automated evaluation suite

## Quick Start

1. **Generate Training Data:**
   ```bash
   python training/data_generator.py --scenarios 1000
   ```

2. **Train Custom Model:**
   ```bash
   python training/train_crew.py --config training/models/fine_tuning_config.yaml
   ```

3. **Evaluate Performance:**
   ```bash
   python training/evaluation_runner.py --model custom --benchmark full
   ```

## Training Objectives

- **Browser Tool Mastery**: Perfect execution of Playwright tools
- **Task Completion**: Never stop early, complete all required actions
- **Pattern Recognition**: Learn optimal navigation sequences
- **Error Recovery**: Handle rate limits and failures gracefully
- **Efficiency**: Minimize LLM calls while maximizing coverage

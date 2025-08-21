#!/bin/bash

# CrewAI Training Setup and Execution Script
# This script sets up the training environment and runs the complete pipeline

echo "🚀 CrewAI Training Pipeline Setup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "✅ Virtual environment activated"

# Install training requirements
echo "📦 Installing training dependencies..."
pip install -r training/requirements.txt

# Create necessary directories
mkdir -p training/datasets
mkdir -p training/models/checkpoints
mkdir -p training/evaluation/results
mkdir -p training/logs

echo "✅ Dependencies installed and directories created"

# Generate training data
echo "🔄 Generating training data..."
python training/data_generator.py --scenarios 500

# Run baseline evaluation
echo "🔄 Running baseline evaluation..."
python training/evaluation/performance_metrics.py --model baseline

# Execute training pipeline
echo "🔄 Starting complete training pipeline..."
python training/training_pipeline.py --step all

echo ""
echo "🎉 Training pipeline completed!"
echo "📊 Check training/TRAINING_REPORT.md for results"
echo "📁 Models saved in training/models/"
echo "📈 Evaluation results in training/evaluation/"

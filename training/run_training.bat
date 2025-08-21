@echo off
REM CrewAI Training Pipeline Setup and Execution Script (Windows)
REM This script sets up the training environment and runs the complete pipeline

echo 🚀 CrewAI Training Pipeline Setup
echo ==================================

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo ✅ Virtual environment activated

REM Install training requirements  
echo 📦 Installing training dependencies...
pip install -r training\requirements.txt

REM Create necessary directories
if not exist "training\datasets" mkdir training\datasets
if not exist "training\models\checkpoints" mkdir training\models\checkpoints
if not exist "training\evaluation\results" mkdir training\evaluation\results
if not exist "training\logs" mkdir training\logs

echo ✅ Dependencies installed and directories created

REM Generate training data
echo 🔄 Generating training data...
python training\data_generator.py --scenarios 500

REM Run baseline evaluation
echo 🔄 Running baseline evaluation...
python training\evaluation\performance_metrics.py --model baseline

REM Execute training pipeline
echo 🔄 Starting complete training pipeline...
python training\training_pipeline.py --step all

echo.
echo 🎉 Training pipeline completed!
echo 📊 Check training\TRAINING_REPORT.md for results
echo 📁 Models saved in training\models\
echo 📈 Evaluation results in training\evaluation\

pause

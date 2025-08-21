import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer, TrainingArguments, Trainer
import yaml
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrewAITrainingConfig:
    """Configuration class for CrewAI training"""
    model_name: str
    learning_rate: float
    batch_size: int
    num_epochs: int
    max_input_length: int
    max_output_length: int
    output_dir: str

class CrewAIDataset(torch.utils.data.Dataset):
    """Custom dataset for CrewAI training data"""
    
    def __init__(self, data_file: str, tokenizer, max_input_len: int, max_output_len: int):
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_output_len = max_output_len
        self.examples = []
        
        # Load training data
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                example = json.loads(line)
                self.examples.append(example)
        
        logger.info(f"Loaded {len(self.examples)} training examples")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Tokenize input and output
        input_encoding = self.tokenizer(
            example['input_prompt'],
            truncation=True,
            padding='max_length',
            max_length=self.max_input_len,
            return_tensors='pt'
        )
        
        output_encoding = self.tokenizer(
            example['expected_output'],
            truncation=True,
            padding='max_length', 
            max_length=self.max_output_len,
            return_tensors='pt'
        )
        
        return {
            'input_ids': input_encoding['input_ids'].squeeze(),
            'attention_mask': input_encoding['attention_mask'].squeeze(),
            'labels': output_encoding['input_ids'].squeeze(),
            'tools_used': example['tools_used'],
            'success_criteria': example['success_criteria'],
            'metadata': example['metadata']
        }

class CrewAIModel(nn.Module):
    """Custom model for CrewAI with specialized components"""
    
    def __init__(self, base_model_name: str, num_tools: int = 50):
        super().__init__()
        
        # Load base model
        self.base_model = AutoModel.from_pretrained(base_model_name)
        self.hidden_size = self.base_model.config.hidden_size
        
        # Custom components for CrewAI
        self.tool_classifier = nn.Linear(self.hidden_size, num_tools)
        self.sequence_tracker = nn.LSTM(self.hidden_size, self.hidden_size // 2, 
                                      batch_first=True, bidirectional=True)
        self.efficiency_scorer = nn.Linear(self.hidden_size, 1)
        
        # Generation head
        self.lm_head = nn.Linear(self.hidden_size, self.base_model.config.vocab_size)
        
        # Custom loss weights
        self.tool_loss_weight = 0.4
        self.sequence_loss_weight = 0.3
        self.generation_loss_weight = 0.3
    
    def forward(self, input_ids, attention_mask, labels=None, **kwargs):
        # Get base model outputs
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state
        
        # Tool prediction
        tool_logits = self.tool_classifier(hidden_states.mean(dim=1))
        
        # Sequence tracking
        sequence_output, _ = self.sequence_tracker(hidden_states)
        
        # Efficiency scoring
        efficiency_score = self.efficiency_scorer(hidden_states.mean(dim=1))
        
        # Language modeling
        lm_logits = self.lm_head(hidden_states)
        
        loss = None
        if labels is not None:
            # Compute multi-component loss
            loss_fct = nn.CrossEntropyLoss()
            
            # Generation loss
            shift_logits = lm_logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            generation_loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), 
                                     shift_labels.view(-1))
            
            # Tool prediction loss (simplified - would need tool labels)
            tool_loss = torch.tensor(0.0, device=input_ids.device)
            
            # Sequence completion loss (simplified)
            sequence_loss = torch.tensor(0.0, device=input_ids.device)
            
            # Combined loss
            loss = (self.generation_loss_weight * generation_loss + 
                   self.tool_loss_weight * tool_loss + 
                   self.sequence_loss_weight * sequence_loss)
        
        return {
            'loss': loss,
            'logits': lm_logits,
            'tool_logits': tool_logits,
            'sequence_output': sequence_output,
            'efficiency_score': efficiency_score
        }

class CrewAITrainer:
    """Training pipeline for CrewAI models"""
    
    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize tokenizer and model
        model_name = self.config['model']['base_model']
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add special tokens for CrewAI
        special_tokens = ['<TOOL>', '<SCREENSHOT>', '<NAVIGATE>', '<CLICK>', '<SAVE>']
        self.tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})
        
        # Initialize model
        self.model = CrewAIModel(model_name)
        self.model.base_model.resize_token_embeddings(len(self.tokenizer))
        
        logger.info(f"Initialized model with {self.model.base_model.num_parameters()} parameters")
    
    def load_datasets(self):
        """Load training, validation, and test datasets"""
        data_config = self.config['data']
        
        self.train_dataset = CrewAIDataset(
            data_config['train_file'],
            self.tokenizer,
            data_config['max_input_length'],
            data_config['max_output_length']
        )
        
        self.val_dataset = CrewAIDataset(
            data_config['validation_file'],
            self.tokenizer,
            data_config['max_input_length'], 
            data_config['max_output_length']
        )
        
        self.test_dataset = CrewAIDataset(
            data_config['test_file'],
            self.tokenizer,
            data_config['max_input_length'],
            data_config['max_output_length']
        )
        
        logger.info("Datasets loaded successfully")
    
    def compute_metrics(self, eval_pred):
        """Compute custom metrics for CrewAI evaluation"""
        predictions, labels = eval_pred
        
        # Decode predictions and labels
        pred_texts = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        label_texts = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Custom metrics
        metrics = {}
        
        # Tool accuracy - count correct tool mentions
        tool_accuracy = 0
        sequence_completion = 0
        response_efficiency = 0
        
        for pred, label in zip(pred_texts, label_texts):
            # Tool accuracy
            pred_tools = self.extract_tools(pred)
            label_tools = self.extract_tools(label)
            if pred_tools == label_tools:
                tool_accuracy += 1
            
            # Sequence completion
            if self.check_sequence_complete(pred):
                sequence_completion += 1
            
            # Response efficiency (shorter is better, but must be complete)
            efficiency = len(label.split()) / max(len(pred.split()), 1)
            response_efficiency += min(efficiency, 1.0)
        
        n_examples = len(pred_texts)
        metrics['tool_accuracy'] = tool_accuracy / n_examples
        metrics['sequence_completion'] = sequence_completion / n_examples  
        metrics['response_efficiency'] = response_efficiency / n_examples
        
        return metrics
    
    def extract_tools(self, text: str) -> List[str]:
        """Extract tool names from text"""
        tools = []
        for tool in ['browser_navigate', 'browser_click', 'browser_take_screenshot', 
                    'browser_wait_for', 'File Writer Tool']:
            if tool in text:
                tools.append(tool)
        return sorted(tools)
    
    def check_sequence_complete(self, text: str) -> bool:
        """Check if sequence appears to be complete"""
        completion_indicators = ['p34', 'screenshot: p34', 'final save', 'completion']
        return any(indicator in text.lower() for indicator in completion_indicators)
    
    def train(self):
        """Run the training process"""
        logger.info("Starting CrewAI training...")
        
        # Load datasets
        self.load_datasets()
        
        # Training arguments
        training_config = self.config['training']
        training_args = TrainingArguments(
            output_dir=self.config['deployment']['output_dir'],
            num_train_epochs=training_config['num_epochs'],
            per_device_train_batch_size=training_config['batch_size'],
            per_device_eval_batch_size=training_config['batch_size'],
            learning_rate=training_config['learning_rate'],
            weight_decay=training_config['weight_decay'],
            logging_steps=10,
            eval_steps=50,
            save_steps=100,
            evaluation_strategy="steps",
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="tool_accuracy",
            greater_is_better=True,
            warmup_steps=training_config['warmup_steps'],
            gradient_accumulation_steps=training_config['gradient_accumulation_steps'],
            dataloader_num_workers=4,
            remove_unused_columns=False
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            compute_metrics=self.compute_metrics,
            tokenizer=self.tokenizer
        )
        
        # Train the model
        trainer.train()
        
        # Save the final model
        trainer.save_model()
        self.tokenizer.save_pretrained(training_args.output_dir)
        
        logger.info("Training completed!")
        
        # Evaluate on test set
        test_results = trainer.evaluate(self.test_dataset)
        logger.info(f"Test results: {test_results}")
        
        return trainer, test_results

def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train CrewAI model")
    parser.add_argument("--config", default="training/models/fine_tuning_config.yaml",
                       help="Path to training configuration file")
    
    args = parser.parse_args()
    
    # Initialize and run training
    trainer = CrewAITrainer(args.config)
    model, results = trainer.train()
    
    print("✅ Training completed successfully!")
    print(f"📊 Final test results: {results}")

if __name__ == "__main__":
    main()

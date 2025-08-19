#!/usr/bin/env python3
"""
Main Entry Point with Simple Configuration

Simplified version using the easy config system.
Just edit config.yaml or run: python simple_config.py

Author: AI Assistant
Version: 2.0
"""

import sys
import os
import traceback

# Add the project root to the Python path so we can import backend modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.config.config import config
from backend.core.generate_outputs import MaintenanceParser, load_inputs, create_comparison_tables



def clear_logs():
    """Clear previous log files before starting new run."""
    import glob
    log_files = glob.glob(f"{config.logs_dir}/*.log")
    for log_file in log_files:
        try:
            # Clear file content instead of deleting the file
            with open(log_file, 'w') as f:
                f.write('')
        except Exception as e:
            print(f"Warning: Could not clear log file {log_file}: {e}")
    
    # Ensure logs directory exists
    os.makedirs(config.logs_dir, exist_ok=True)


def main():
    """Main execution with simple configuration."""
    try:
        print("🚀 Industrial Maintenance Voice Note Parser")
        print("=" * 50)
        
        # Single file logging is configured centrally in config module

        # Strictly validate API key for the selected provider
        try:
            _ = config.get_api_config(config.ai_provider)
            print(f"✅ Environment validation passed for provider: {config.ai_provider}")
        except ValueError as e:
            print(f"❌ Environment validation failed for provider '{config.ai_provider}': {e}")
            print(f"Please set the required API key for '{config.ai_provider}' in your .env file.")
            sys.exit(1)

        # Clear previous logs
        print("📝 Clearing previous logs...")
        clear_logs()
        print("✅ Previous logs cleared")
        
        # Use default dataset from config (full dataset)
        dataset_file = f'{config.inputs_dir}/inputs_only.json'
        
        # Display current configuration
        print(f"\n🎯 Processing Configuration:")
        print(f"   📁 Dataset: {dataset_file}")
        print(f"   🤖 AI Provider: {config.ai_provider}")
        print(f"   🧠 Model: {config.model}")
        print(f"   🌡️  Temperature: {config.temperature}")
        print()
        
        # Initialize parser
        print("🔧 Initializing AI provider...")
        parser = MaintenanceParser(config.ai_provider, config.model, config.temperature)
        parser.initialize_ai_provider()
        print("✅ AI provider initialized successfully")
        
        # Load inputs
        print(f"\n📂 Loading inputs from {dataset_file}...")
        inputs = load_inputs(dataset_file)
        print(f"✅ Loaded {len(inputs)} inputs")
        
        # Generate outputs
        print(f"\n🚀 Starting AI processing...")
        results = parser.generate_outputs(inputs)
        
        # Save results
        output_filename = f"{config.outputs_dir}/system_generated_outputs.json"
        print(f"\n💾 Saving results...")
        parser.save_results(results, output_filename)
        print(f"✅ Results saved to: {output_filename}")
        
        # Create comparison tables
        print(f"\n📊 Creating comparison tables...")
        create_comparison_tables(results)
        print(f"✅ Comparison tables created")
        
        print(f"\n🎉 Processing completed successfully!")
        print(f"📁 Results saved to: {output_filename}")
        print(f"📊 Tables saved to: {config.outputs_dir}/")
        print(f"📝 Logs saved to: {config.logs_dir}/")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

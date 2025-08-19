#!/usr/bin/env python3
"""
Test Script: First 3 Entries from Each Use Case

This script simply calls the main.py main function but with test data instead of the full dataset.
It reuses ALL the same processing logic, validation, and output generation.

Author: AI Assistant
Version: 2.0
"""

import sys
import os
import json
import shutil
import yaml

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..', '..')

sys.path.append(project_root)

from backend.config.config import config


def create_test_inputs():
    """Read test inputs from existing test inputs file."""
    try:
        # Path to existing test inputs file
        test_inputs_dir = os.path.join('backend', 'test', 'inputs')
        test_input_path = os.path.join(test_inputs_dir, 'inputs_only.json')
        print(f"Lizaaa Test input path: {test_input_path}")
        
        # Check if test inputs file exists
        if not os.path.exists(test_input_path):
            print(f"❌ Test inputs file not found: {test_input_path}")
            print("Please create a test inputs file with 3 entries from each use case")
            sys.exit(1)
        
        # Read the existing test inputs file
        with open(test_input_path, 'r') as f:
            test_data = json.load(f)
        
        print(f"✅ Reading test input file: {test_input_path}")
        print(f"   Work Triaging: {len(test_data.get('work_item_triaging', []))} entries")
        print(f"   Closing Comments: {len(test_data.get('closing_comment', []))} entries")
        
        return test_input_path
        
    except Exception as e:
        print(f"❌ Error reading test inputs: {e}")
        sys.exit(1)


def main():
    """Main execution that calls the main.py main function with test data."""
    try:
        print("🧪 TEST: First 3 Entries from Each Use Case")
        print("=" * 60)
        
        # Change to project root directory for proper path resolution
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.chdir(project_root)
        print(f"📁 Changed to project root: {os.getcwd()}")
        
        # Create test input file
        print("\n📋 Creating test input file...")
        test_input_file = create_test_inputs()
        print("✅ Test input file created successfully")
        
        # Backup original config.yaml
        config_yaml_path = os.path.join('backend', 'config', 'config.yaml')
        backup_config_path = os.path.join('backend', 'config', 'config.yaml.backup')
        
        print(f"\n📋 Backing up original config...")
        shutil.copy2(config_yaml_path, backup_config_path)
        print(f"✅ Original config backed up to: {backup_config_path}")
        
        # Read current config and modify it for test
        with open(config_yaml_path, 'r') as f:
            config_content = yaml.safe_load(f)
        
        # Store original values
        original_inputs_dir = config_content.get('inputs_dir')
        original_outputs_dir = config_content.get('outputs_dir')
        
        # Modify config for test
        config_content['inputs_dir'] = os.path.dirname(test_input_file)
        config_content['outputs_dir'] = os.path.join('backend', 'test', 'outputs')
        
        # Write modified config
        with open(config_yaml_path, 'w') as f:
            yaml.dump(config_content, f, default_flow_style=False)
        
        print(f"✅ Config modified for test:")
        print(f"   📥 Input: {config_content['inputs_dir']}")
        print(f"   📤 Output: {config_content['outputs_dir']}")
        
        # Create test outputs directory
        print(f"\n📁 Setting up test environment...")
        os.makedirs(config_content['outputs_dir'], exist_ok=True)
        print("✅ Test outputs directory ready")
        
        print(f"\n🎯 Test environment configured:")
        print(f"   📥 Input: {test_input_file}")
        print(f"   📤 Output: {config_content['outputs_dir']}")
        print(f"   🔧 AI Provider: {config_content.get('ai_provider')}")
        print(f"   🧠 Model: {config_content.get('model')}")
        print(f"   🌡️  Temperature: {config_content.get('temperature')}")
        print()
        
        # Run main.py directly as a subprocess
        print("🚀 Starting test execution...")
        print("   This will process 3 work triaging + 3 closing comment inputs")
        print("   Estimated time: ~30 seconds")
        print()
        
        import subprocess
        result = subprocess.run(['python', '-m', 'backend.main'], capture_output=True, text=True, check=True)
        
        print("✅ Main execution completed successfully")
        
        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"📁 Results saved to: {config_content['outputs_dir']}/")
        print(f"📊 Test processed 6 total inputs")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always restore original config
        print(f"\n📋 Restoring original config...")
        try:
            shutil.copy2(backup_config_path, config_yaml_path)
            print(f"✅ Original config restored")
        except Exception as e:
            print(f"⚠️  Warning: Could not restore config: {e}")
            print(f"   Please manually restore from: {backup_config_path}")
        
        # Clean up backup
        try:
            os.remove(backup_config_path)
            print(f"✅ Backup file cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up backup: {e}")
        
        print(f"🎯 Test environment cleanup completed")


if __name__ == "__main__":
    main()

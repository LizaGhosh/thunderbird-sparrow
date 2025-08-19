#!/usr/bin/env python3
"""
Industrial Maintenance Voice Note Parser

This script processes voice transcriptions and converts them into structured work items
using AI providers (Claude or Gemini). It generates comparison tables and performance metrics.

Author: AI Assistant
Version: 2.0
"""

import json
import os
from typing import Dict, List, Any
import pandas as pd

from . import create_ai_provider
from ..config.config import config


class MaintenanceParser:
    """Main class for parsing maintenance voice notes using AI providers."""
    
    def __init__(self, ai_provider_name: str, model: str, temperature: float):
        """
        Initialize the maintenance parser.
        
        Args:
            ai_provider_name: Name of AI provider ('claude' or 'gemini')
            model: Specific model to use
            temperature: Temperature setting for AI generation
        """
        self.ai_provider_name = ai_provider_name
        self.model = model
        self.temperature = temperature
        self.ai_provider = None
        self.results = []
        
    def initialize_ai_provider(self) -> None:
        """Initialize the AI provider with specified configuration."""
        try:
            self.ai_provider = create_ai_provider(
                provider_name=self.ai_provider_name,
                model=self.model,
                temperature=self.temperature
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI provider: {e}")
    
    def process_work_triaging(self, inputs: List[Dict]) -> List[Dict]:
        """Process work triaging inputs and return results."""
        results = []
        total_inputs = len(inputs)
        
        print(f"\n🔍 Processing {total_inputs} work triaging inputs...")
        print("=" * 60)
        
        for i, input_data in enumerate(inputs, 1):
            test_id = input_data.get('test_id', f'wt_{i:03d}')
            text = input_data.get('text', '')
            
            # Progress indicator with current input number
            progress_pct = (i / total_inputs) * 100
            print(f"[{i:2d}/{total_inputs}] [{progress_pct:5.1f}%] 🎯 Processing {test_id}...")
            
            try:
                # Show thinking status
                print(f"    🤔 Analyzing work intent...")
                result = self.ai_provider.analyze_work_intent(text, test_id)
                
                # Show validation status
                print(f"    ✅ AI response received, validating...")
                from .validation import validate_work_triaging_output
                is_valid = validate_work_triaging_output(result, test_id)
                
                if not is_valid:
                    result['processing_status'] = 'validation_failed'
                    print(f"    ⚠️  Validation failed for {test_id}")
                else:
                    result['processing_status'] = 'success'
                    print(f"    🎉 Successfully processed {test_id}")
                
                results.append(result)
                
            except Exception as e:
                print(f"    ❌ Error processing {test_id}: {e}")
                error_result = {
                    'test_id': test_id,
                    'test_focus': input_data.get('test_focus', ''),
                    'input_preview': text[:100] + "..." if len(text) > 100 else text,
                    'processing_status': 'failed',
                    'error': str(e)
                }
                results.append(error_result)
        
        print(f"\n✅ Work triaging completed: {len(results)} results")
        return results
    
    def process_closing_comments(self, inputs: List[Dict]) -> List[Dict]:
        """Process closing comment inputs and return results."""
        results = []
        total_inputs = len(inputs)
        
        print(f"\n💬 Processing {total_inputs} closing comment inputs...")
        print("=" * 60)
        
        for i, input_data in enumerate(inputs, 1):
            test_id = input_data.get('test_id', f'cc_{i:03d}')
            text = input_data.get('text', '')
            
            # Progress indicator with current input number
            progress_pct = (i / total_inputs) * 100
            print(f"[{i:2d}/{total_inputs}] [{progress_pct:5.1f}%] 🎯 Processing {test_id}...")
            
            try:
                # Show thinking status
                print(f"    🤔 Generating closing comment...")
                result = self.ai_provider.generate_closing_comment(text, test_id)
                
                # Show validation status
                print(f"    ✅ AI response received, validating...")
                from .validation import validate_closing_comment_output
                is_valid = validate_closing_comment_output(result, test_id)
                
                if not is_valid:
                    result['processing_status'] = 'validation_failed'
                    print(f"    ⚠️  Validation failed for {test_id}")
                else:
                    result['processing_status'] = 'success'
                    print(f"    🎉 Successfully processed {test_id}")
                
                results.append(result)
                
            except Exception as e:
                print(f"    ❌ Error processing {test_id}: {e}")
                error_result = {
                    'test_id': test_id,
                    'test_focus': input_data.get('test_focus', ''),
                    'input_preview': text[:100] + "..." if len(text) > 100 else text,
                    'processing_status': 'failed',
                    'error': str(e)
                }
                results.append(error_result)
        
        print(f"\n✅ Closing comments completed: {len(results)} results")
        return results
    
    def generate_outputs(self, inputs: List[Dict]) -> Dict[str, Any]:
        """Generate all outputs and return structured results in exact Attachment B format."""
        print(f"\n🚀 Starting voice note processing...")
        print(f"📊 Total inputs to process: {len(inputs)}")
        print("=" * 60)
        
        # Separate inputs by type
        work_triaging_inputs = []
        closing_comment_inputs = []
        
        for input_item in inputs:
            test_id = input_item['test_id']
            if test_id.startswith('wt_'):
                work_triaging_inputs.append(input_item)
            elif test_id.startswith('cc_'):
                closing_comment_inputs.append(input_item)
            else:
                # Default to work triaging for unknown types
                work_triaging_inputs.append(input_item)
        
        print(f"📋 Input breakdown:")
        print(f"   🎯 Work Triaging: {len(work_triaging_inputs)} inputs")
        print(f"   💬 Closing Comments: {len(closing_comment_inputs)} inputs")
        print()
        
        # Process work triaging inputs
        print("🔄 Phase 1: Processing Work Triaging...")
        work_results = self.process_work_triaging(work_triaging_inputs)
        
        # Process closing comment inputs
        print("\n🔄 Phase 2: Processing Closing Comments...")
        closing_results = self.process_closing_comments(closing_comment_inputs)
        
        print("\n🔄 Phase 3: Collating Results...")
        
        # Transform directly to Attachment B format with system_output instead of expected_output
        work_item_triaging_results = []
        closing_comment_results = []
        
        # Process work triaging results
        for i, work_result in enumerate(work_results):
            # Extract only the AI output (remove metadata)
            ai_output = {k: v for k, v in work_result.items() 
                        if k not in ['processing_status', 'error']}
            
            # Get metadata from original input
            original_input = work_triaging_inputs[i]
            
            work_item_triaging_results.append({
                'id': original_input['test_id'],
                'input': original_input['text'],
                'system_output': ai_output,
                'test_focus': original_input['test_focus']
            })
        
        # Process closing comment results
        for i, closing_result in enumerate(closing_results):
            # Extract only the AI output (remove metadata)
            ai_output = {k: v for k, v in closing_result.items() 
                        if k not in ['processing_status', 'error']}
            
            # Get metadata from original input
            original_input = closing_comment_inputs[i]
            
            closing_comment_results.append({
                'id': original_input['test_id'],
                'input': original_input['text'],
                'system_output': ai_output,
                'test_focus': original_input['test_focus']
            })
        
        print("✅ Results collation completed!")
        print(f"   📊 Work Triaging: {len(work_item_triaging_results)} results")
        print(f"   📊 Closing Comments: {len(closing_comment_results)} results")
        
        return {
            'work_item_triaging': work_item_triaging_results,
            'closing_comment': closing_comment_results
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = 'system_generated_outputs.json') -> None:
        """Save results to JSON file in Attachment B format."""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            # Results saved successfully
        except Exception as e:
            raise IOError(f"Error saving results: {e}")


def load_inputs(filename: str = 'backend/data/inputs/inputs_only.json') -> List[Dict]:
    """Load input data from JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Transform the data structure to match expected format
        transformed_inputs = []
        
        # Process work item triaging inputs
        if 'work_item_triaging' in data:
            for item in data['work_item_triaging']:
                transformed_inputs.append({
                    'test_id': item['id'],
                    'text': item['input'],
                    'test_focus': item['test_focus']
                })
        
        # Process closing comment inputs (note: key is "closing_comment" not "closing_comments")
        if 'closing_comment' in data:
            for item in data['closing_comment']:
                transformed_inputs.append({
                    'test_id': item['id'],
                    'text': item['input'],
                    'test_focus': item['test_focus']
                })
        
        # Successfully loaded input data
        return transformed_inputs
        
    except Exception as e:
        raise FileNotFoundError(f"Error loading inputs from {filename}: {e}")


def create_comparison_tables(results: Dict[str, Any]) -> None:
    """Create comparison tables between system and expected outputs."""
    # Creating comparison tables
    
    # Import config to get output directory
    from ..config.config import config
    
    # Load expected outputs
    expected_outputs_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'dataset', 'Thunderbird-Take-Home-Attachment-B.json')
    try:
        with open(expected_outputs_file, 'r') as f:
            expected_data = json.load(f)
        # Expected outputs loaded successfully
    except Exception as e:
        raise FileNotFoundError(f"Error loading expected outputs: {e}")
    
    # Extract work triaging results from new structure
    work_results = results.get('work_item_triaging', [])
    
    # Create summary table
    summary_data = []
    
    # Create detailed work triaging table
    work_data = []
    
    # Create detailed closing comments table
    closing_data = []
    
    for result in work_results:
        test_id = result.get('id', '')
        test_focus = result.get('test_focus', '')
        input_preview = result.get('input', '')
        processing_status = 'success'  # Default status for work triaging
        
        # Get system output
        system_output = result.get('system_output', {})
        closing_output = None  # No closing comment for work triaging
        
        # Get expected output from Attachment B structure
        expected_output = None
        if 'work_item_triaging' in expected_data:
            for exp in expected_data['work_item_triaging']:
                if exp.get('id') == test_id:
                    expected_output = exp.get('expected_output', {})
                    break
        
        # Extract category from system output structure
        system_category = 'unknown'
        if system_output:
            if system_output.get('work_requests') and len(system_output['work_requests']) > 0:
                system_category = 'work_request'
            elif system_output.get('work_orders') and len(system_output['work_orders']) > 0:
                system_category = 'work_order'
            elif system_output.get('inspection_tasks') and len(system_output['inspection_tasks']) > 0:
                system_category = 'inspection_task'
            elif system_output.get('general_tasks') and len(system_output['general_tasks']) > 0:
                system_category = 'general_task'
        
        # Extract category from expected output (Attachment B format)
        expected_category = 'unknown'
        if expected_output:
            if expected_output.get('work_requests'):
                expected_category = 'work_request'
            elif expected_output.get('work_orders'):
                expected_category = 'work_order'
            elif expected_output.get('inspection_tasks'):
                expected_category = 'inspection_task'
            elif expected_output.get('general_tasks'):
                expected_category = 'general_task'
        
        # Determine if categories match
        category_match = system_category == expected_category
        
        # Summary data
        summary_data.append({
            'test_id': test_id,
            'test_focus': test_focus,
            'input_preview': input_preview,
            'system_category': system_category,
            'expected_category': expected_category,
            'category_match': category_match,
            'processing_status': processing_status
        })
        
        # Detailed work triaging data - using Attachment B field names
        # Always add entry to work_data, even if system_output is empty
        # Extract expected data from the populated array
        expected_item = None
        if expected_output:
            if expected_output.get('work_requests'):
                expected_item = expected_output['work_requests'][0]
            elif expected_output.get('work_orders'):
                expected_item = expected_output['work_orders'][0]
            elif expected_output.get('inspection_tasks'):
                expected_item = expected_output['inspection_tasks'][0]
            elif expected_output.get('general_tasks'):
                expected_item = expected_output['general_tasks'][0]
        
        # Extract data from the populated array in system_output
        system_item = None
        if system_output.get('work_requests'):
            system_item = system_output['work_requests'][0]
        elif system_output.get('work_orders'):
            system_item = system_output['work_orders'][0]
        elif system_output.get('inspection_tasks'):
            system_item = system_output['inspection_tasks'][0]
        elif system_output.get('general_tasks'):
            system_item = system_output['general_tasks'][0]
        
        # Always add to work_data, even if system_item is None (empty outputs)
        work_data.append({
            'Test_ID': test_id,
            'Test_Focus': test_focus,
            'Input_Preview': input_preview,
            'Processing_Status': processing_status,
            'System_Output_Type': system_category,
            'Expected_Output_Type': expected_category,
            'Type_Match': '✅' if category_match else '❌',
            'System_Title': system_item.get('title', 'N/A') if system_item else 'N/A',
            'Expected_Title': expected_item.get('title', 'N/A') if expected_item else 'N/A',
            'System_Asset_ID': system_item.get('asset_id', 'N/A') if system_item else 'N/A',
            'Expected_Asset_ID': expected_item.get('asset_id', 'N/A') if expected_item else 'N/A',
            'Asset_Match': '✅' if (expected_item and system_item and system_item.get('asset_id') == expected_item.get('asset_id')) else '❌',
            'System_Assigned_To': system_item.get('assigned_to', 'N/A') if system_item else 'N/A',
            'Expected_Assigned_To': expected_item.get('assigned_to', 'N/A') if expected_item else 'N/A',
            'Assigned_Match': '✅' if (expected_item and system_item and system_item.get('assigned_to') == expected_item.get('assigned_to')) else '❌',
            'System_Work_Type_ID': system_item.get('work_type_id', 'N/A') if system_item else 'N/A',
            'Expected_Work_Type_ID': expected_item.get('work_type_id', 'N/A') if expected_item else 'N/A',
            'Work_Type_Match': '✅' if (expected_item and system_item and system_item.get('work_type_id') == expected_item.get('work_type_id')) else '❌',
            'System_Status': system_item.get('status', 'N/A') if system_item else 'N/A',
            'Expected_Status': expected_item.get('status', 'N/A') if expected_item else 'N/A',
            'Status_Match': '✅' if (expected_item and system_item and system_item.get('status') == expected_item.get('status')) else '❌',
            'System_Description': system_item.get('description', 'N/A') if system_item else 'N/A',
            'Expected_Description': expected_item.get('description', 'N/A') if expected_item else 'N/A',
            'Has_User_Query': 'Yes' if (system_item and system_item.get('user_query')) else 'No'
        })
        
        # Detailed closing comments data - using Attachment B structure
        if closing_output:
            # Get expected closing comment data from Attachment B
            expected_closing = None
            if 'closing_comment' in expected_data:
                for exp in expected_data['closing_comment']:
                    if exp.get('id') == test_id:
                        expected_closing = exp.get('expected_output', {})
                        break
            
            # Convert downtime values to float for comparison
            system_downtime = closing_output.get('downtime_hours')
            expected_downtime = expected_closing.get('actual_downtime_hours') if expected_closing else None
            
            # Convert to float, handling None values
            try:
                system_downtime_float = float(system_downtime) if system_downtime is not None else None
            except (ValueError, TypeError):
                system_downtime_float = None
                
            try:
                expected_downtime_float = float(expected_downtime) if expected_downtime is not None else None
            except (ValueError, TypeError):
                expected_downtime_float = None
            
            # Determine if downtime values match
            downtime_match = '✅ Match' if system_downtime_float == expected_downtime_float else '❌ Mismatch'
            
            closing_data.append({
                'Test_ID': test_id,
                'Test_Focus': test_focus,
                'Input_Preview': input_preview,
                'System_Comment': closing_output.get('closing_comment', 'N/A'),
                'Expected_Comment': expected_closing.get('closing_comment', 'N/A') if expected_closing else 'N/A',
                'System_Downtime_Hours': system_downtime_float,
                'Expected_Downtime_Hours': expected_downtime_float,
                'Downtime_Match': downtime_match,
                'Processing_Status': processing_status
            })
    
    # Now process closing comment results separately
    closing_results = results.get('closing_comment', [])
    for result in closing_results:
        test_id = result.get('id', '')
        test_focus = result.get('test_focus', '')
        input_preview = result.get('input', '')
        processing_status = 'success'  # Default status for closing comments
        
        # Get system output (closing comment data)
        system_output = result.get('system_output', {})
        
        # Get expected closing comment data from Attachment B
        expected_closing = None
        if 'closing_comment' in expected_data:
            for exp in expected_data['closing_comment']:
                if exp.get('id') == test_id:
                    expected_closing = exp.get('expected_output', {})
                    break
        
        # Convert downtime values to float for comparison
        system_downtime = system_output.get('actual_downtime_hours')
        expected_downtime = expected_closing.get('actual_downtime_hours') if expected_closing else None
        
        # Convert to float, handling None values
        try:
            system_downtime_float = float(system_downtime) if system_downtime is not None else None
        except (ValueError, TypeError):
            system_downtime_float = None
            
        try:
            expected_downtime_float = float(expected_downtime) if expected_downtime is not None else None
        except (ValueError, TypeError):
            expected_downtime_float = None
        
        # Determine if downtime values match
        downtime_match = '✅ Match' if system_downtime_float == expected_downtime_float else '❌ Mismatch'
        
        closing_data.append({
            'Test_ID': test_id,
            'Test_Focus': test_focus,
            'Input_Preview': input_preview,
            'System_Comment': system_output.get('closing_comment', 'N/A'),
            'Expected_Comment': expected_closing.get('closing_comment', 'N/A') if expected_closing else 'N/A',
            'System_Downtime_Hours': system_downtime_float,
            'Expected_Downtime_Hours': expected_downtime_float,
            'Downtime_Match': downtime_match,
            'Processing_Status': processing_status
        })
    
    # Create and save summary table
    summary_df = pd.DataFrame(summary_data)
    summary_filename = f'{config.outputs_dir}/summary_table.csv'
    summary_df.to_csv(summary_filename, index=False)
    
    # Create and save detailed work triaging table
    if work_data:
        work_df = pd.DataFrame(work_data)
        work_filename = f'{config.outputs_dir}/work_triaging.csv'
        work_df.to_csv(work_filename, index=False)
    
    # Create and save detailed closing comments table
    if closing_data:
        closing_df = pd.DataFrame(closing_data)
        closing_filename = f'{config.outputs_dir}/closing_comments.csv'
        closing_df.to_csv(closing_filename, index=False)
    
    # Summary statistics calculated successfully













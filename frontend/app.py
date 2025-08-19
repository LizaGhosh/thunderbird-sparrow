#!/usr/bin/env python3
"""
Web Interface for Industrial Maintenance Voice Note Parser

Flask application providing:
- Configuration interface (model, temperature)
- Test execution (short test or full dataset)
- Results dashboard with metrics and detailed outputs
- Real-time progress tracking during execution
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, send_file
import json
import os
import sys
import subprocess
import tempfile
import shutil
import threading
import time
from datetime import datetime
import glob
import pandas as pd
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.config import config as global_config
from backend.core.generate_outputs import create_comparison_tables
from backend.core.metrics import MetricsCalculator

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to store current results
current_results = None
current_config = None
execution_progress = {
    'status': 'idle',
    'current_step': '',
    'progress': 0,
    'total_steps': 0,
    'current_input': 0,
    'total_inputs': 0,
    'logs': []
}

def add_progress_log(message, step_type='info'):
    """Add a progress log message with timestamp."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': step_type
    }
    execution_progress['logs'].append(log_entry)
    # Keep only last 50 logs
    if len(execution_progress['logs']) > 50:
        execution_progress['logs'] = execution_progress['logs'][-50:]

def update_progress(status, current_step, progress=None, total_steps=None, current_input=None, total_inputs=None):
    """Update progress information."""
    execution_progress['status'] = status
    execution_progress['current_step'] = current_step
    if total_steps is not None:
        execution_progress['total_steps'] = total_steps
    if current_input is not None:
        execution_progress['current_input'] = current_input
    if total_inputs is not None:
        execution_progress['total_inputs'] = total_inputs

def clear_logs_before_execution():
    """Clear log files before starting execution to get clean baseline."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'backend', 'logs')
        
        if os.path.exists(logs_dir):
            log_files = glob.glob(os.path.join(logs_dir, '*.log'))
            for log_file in log_files:
                try:
                    # Clear the log file content
                    with open(log_file, 'w') as f:
                        f.write('')
                except Exception as e:
                    continue
    except Exception as e:
        pass

def run_execution_with_progress(test_type):
    """Run execution in background thread with progress updates."""
    global current_results, current_config
    
    try:
        # Prepare merged config (YAML defaults + any user overrides) for this run
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(project_root, 'backend', 'config')
        config_path = os.path.join(config_dir, 'config.yaml')
        backup_path = os.path.join(config_dir, 'config.yaml.bak')

        # Build default YAML-backed config dict
        yaml_defaults = {
            'ai_provider': getattr(global_config, 'ai_provider', None),
            'model': getattr(global_config, 'model', None),
            'temperature': getattr(global_config, 'temperature', None),
            'parallel_processing': getattr(global_config, 'parallel_processing', False),
            'validate_outputs': getattr(global_config, 'validate_outputs', True),
            'inputs_dir': getattr(global_config, 'inputs_dir', 'backend/data/inputs'),
            'outputs_dir': getattr(global_config, 'outputs_dir', 'backend/data/outputs'),
            'logs_dir': getattr(global_config, 'logs_dir', 'backend/logs'),
        }

        # Apply user overrides if present
        merged_config = dict(yaml_defaults)
        if current_config:
            for k in ('ai_provider', 'model', 'temperature'):
                if k in current_config and current_config[k] not in (None, ''):
                    merged_config[k] = current_config[k]

        # Safely backup and write merged YAML for the duration of the run
        import yaml as _yaml
        try:
            if os.path.exists(config_path):
                shutil.copyfile(config_path, backup_path)
            with open(config_path, 'w') as f:
                f.write("# Generated for this execution. Original will be restored after run.\n\n")
                _yaml.safe_dump(merged_config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            add_progress_log(f'❌ Failed to prepare configuration for execution: {e}', 'error')
            update_progress('failed', 'Failed')
            return

        update_progress('running', 'Initializing...', current_input=0)
        add_progress_log('🚀 Starting execution...', 'start')
        
        # Clear logs before starting to get clean baseline
        clear_logs_before_execution()
        add_progress_log('📝 Logs cleared, starting fresh execution...', 'info')
        
        if test_type == 'short_test':
            add_progress_log('🧪 Running short test (3 entries each)', 'info')
            update_progress('running', 'Running Short Test', current_input=0, total_inputs=6)
            
            # Start monitoring logs for real progress
            start_log_monitoring(test_type)
            
            # Run short test
            result = subprocess.run(
                ['python', 'backend/test/test_first_three.py'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                add_progress_log('✅ Short test completed successfully', 'success')
                update_progress('running', 'Loading Results', current_input=6, total_inputs=6)
                
                # Load test results
                test_output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'test', 'outputs', 'system_generated_outputs.json')
                with open(test_output_path, 'r') as f:
                    current_results = json.load(f)
                current_config = {'test_type': 'Short Test (3 entries each)'}
                
                add_progress_log('📊 Results loaded successfully', 'success')
                update_progress('completed', 'Completed', current_input=6, total_inputs=6)
                
            else:
                add_progress_log(f'❌ Test failed: {result.stderr}', 'error')
                update_progress('failed', 'Failed')
                
        elif test_type == 'full_dataset':
            add_progress_log('📊 Running full dataset (25 entries each)', 'info')
            update_progress('running', 'Running Full Dataset', current_input=0, total_inputs=50)
            
            # Start monitoring logs for real progress
            start_log_monitoring(test_type)
            # Run full dataset
            result = subprocess.run(
                ['python', 'backend/main.py'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if result.returncode == 0:
                add_progress_log('✅ Full dataset completed successfully', 'success')
                update_progress('running', 'Loading Results', current_input=50, total_inputs=50)
                
                # Load full results
                full_output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'data', 'outputs', 'system_generated_outputs.json')
                with open(full_output_path, 'r') as f:
                    current_results = json.load(f)
                current_config = {'test_type': 'Full Dataset (25 entries each)'}
                
                add_progress_log('📊 Results loaded successfully', 'success')
                update_progress('completed', 'Completed', current_input=50, total_inputs=50)
                
            else:
                add_progress_log(f'❌ Full dataset failed: {result.stderr}', 'error')
                update_progress('failed', 'Failed')
                
    except Exception as e:
        add_progress_log(f'❌ Execution error: {str(e)}', 'error')
        update_progress('failed', 'Error')
    finally:
        # Restore original YAML config if backup exists
        try:
            if os.path.exists(backup_path):
                shutil.move(backup_path, config_path)
        except Exception:
            # If restore fails, leave merged config in place and log
            add_progress_log('⚠️ Could not restore original config.yaml after execution', 'warning')

def start_log_monitoring(test_type):
    """Start monitoring log files for real-time progress updates."""
    def monitor_logs():
        import time
        import glob
        
        # Get the logs directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'backend', 'logs')
        
        # Track processed items
        processed_items = set()
        last_log_check = time.time()
        
        # Set initial progress
        if test_type == 'short_test':
            total_expected = 6  # 3 work triaging + 3 closing comments
        else:
            total_expected = 50  # 25 work triaging + 25 closing comments
        
        # Track phases
        work_triaging_count = 0
        closing_comment_count = 0
        
        while execution_progress['status'] == 'running':
            try:
                # Check for new log entries more frequently
                current_time = time.time()
                if current_time - last_log_check >= 0.5:  # Check every 500ms for more responsiveness
                    last_log_check = current_time
                    
                    # Look for log files
                    log_files = glob.glob(os.path.join(logs_dir, '*.log'))
                    
                    for log_file in log_files:
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                
                            # Count processed items from logs
                            for line in lines:
                                if 'ANALYZE_WORK_INTENT' in line or 'GENERATE_CLOSING_COMMENT' in line:
                                    # Extract timestamp to create unique identifier
                                    timestamp = line.split(' - ')[0]
                                    if timestamp not in processed_items:
                                        processed_items.add(timestamp)
                                        
                                        # Update progress based on actual items processed
                                        current_count = len(processed_items)
                                        
                                        # Update progress with current item count
                                        update_progress('running', f'Processing item {current_count}/{total_expected}', 
                                                      current_input=current_count, total_inputs=total_expected)
                                        
                                        # Add progress log with more detail
                                        if 'ANALYZE_WORK_INTENT' in line:
                                            work_triaging_count += 1
                                            add_progress_log(f'🎯 Work triaging item {work_triaging_count}/{total_expected//2} completed', 'success')
                                        else:
                                            closing_comment_count += 1
                                            add_progress_log(f'💬 Closing comment item {closing_comment_count}/{total_expected//2} completed', 'success')
                                        
                        except Exception as e:
                            continue
                    
            except Exception as e:
                continue
            
            time.sleep(0.2)  # Smaller delay for more responsive updates
    
    # Start log monitoring in a separate thread
    log_thread = threading.Thread(target=monitor_logs)
    log_thread.daemon = True
    log_thread.start()

@app.route('/')
def index():
    """Main configuration page."""
    return render_template('index.html')

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    """Configuration page for setting model parameters."""
    if request.method == 'POST':
        # Merge user inputs with YAML defaults (YAML is default, user input overrides per-field)
        try:
            ai_provider_input = (request.form.get('ai_provider') or '').strip()
            model_input = (request.form.get('model') or '').strip()
            temperature_input = (request.form.get('temperature') or '').strip()

            ai_provider = ai_provider_input or getattr(global_config, 'ai_provider', None)
            model = model_input or getattr(global_config, 'model', None)

            # Parse temperature if provided, else fallback to YAML
            if temperature_input:
                try:
                    temperature = float(temperature_input)
                except ValueError:
                    temperature = getattr(global_config, 'temperature', 0.0)
            else:
                temperature = getattr(global_config, 'temperature', 0.0)

            # Stash merged config for this session/run (do not write back to YAML)
            global current_config
            current_config = {
                'ai_provider': ai_provider,
                'model': model,
                'temperature': temperature
            }

            return redirect(url_for('run_tests'))
        except Exception as e:
            return render_template('configure.html', config=global_config, error=str(e))
    
    # Load current config
    try:
        # Use global YAML-backed configuration as defaults for the form
        return render_template('configure.html', config=global_config)
    except Exception as e:
        return render_template('configure.html', config=None, error=str(e))

@app.route('/run_tests')
def run_tests():
    """Page to choose between short test and full dataset."""
    return render_template('run_tests.html')

@app.route('/execute', methods=['POST'])
def execute():
    """Execute the selected test type."""
    global execution_progress
    
    test_type = request.form.get('test_type')
    
    # Reset progress
    execution_progress = {
        'status': 'idle',
        'current_step': '',
        'total_steps': 0,
        'current_input': 0,
        'total_inputs': 0,
        'logs': []
    }
    
    # Start execution in background thread
    thread = threading.Thread(target=run_execution_with_progress, args=(test_type,))
    thread.daemon = True
    thread.start()
    
    # Return success response for AJAX
    return jsonify({'success': True, 'message': 'Execution started'})

@app.route('/execute/status')
def execute_status():
    """Get current execution status for AJAX updates."""
    return jsonify(execution_progress)

@app.route('/results')
def results():
    """Results dashboard page."""
    global current_results, current_config
    
    if current_results is None:
        return redirect(url_for('index'))
    
    # Determine which directory to load CSV tables from based on test type
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if this was a short test or full dataset
    if current_config and 'Short Test' in current_config.get('test_type', ''):
        # Short test - load from backend/test/outputs
        outputs_dir = os.path.join(project_root, 'backend', 'test', 'outputs')
    else:
        # Full dataset - load from backend/data/outputs
        outputs_dir = os.path.join(project_root, 'backend', 'data', 'outputs')
    
    # Load work triaging table
    work_triaging_table = None
    try:
        work_path = os.path.join(outputs_dir, 'work_triaging.csv')
        if os.path.exists(work_path):
            import pandas as pd
            work_triaging_table = pd.read_csv(work_path).to_dict('records')
    except Exception as e:
        print(f"Could not load work triaging table: {e}")
    
    # Load closing comments table
    closing_comments_table = None
    try:
        closing_path = os.path.join(outputs_dir, 'closing_comments.csv')
        if os.path.exists(closing_path):
            import pandas as pd
            closing_comments_table = pd.read_csv(closing_path).to_dict('records')
    except Exception as e:
        print(f"Could not load closing comments table: {e}")
    
    # Calculate metrics using MetricsCalculator for consistency
    metrics_calculator = MetricsCalculator()
    
    # Prepare CSV data for accuracy calculations
    csv_data = {}
    if work_triaging_table:
        csv_data['work_triaging'] = work_triaging_table
    if closing_comments_table:
        csv_data['closing_comments'] = closing_comments_table
    
    metrics = metrics_calculator.calculate_all_metrics(current_results)
    
    return render_template('results.html', 
                         metrics=metrics, 
                         config=current_config,
                         results=current_results,
                         work_triaging_table=work_triaging_table,
                         closing_comments_table=closing_comments_table)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics data."""
    global current_results
    
    if current_results is None:
        return jsonify({'error': 'No results available'}), 404
    
    metrics_calculator = MetricsCalculator()
    
    # Load CSV data for accuracy calculations
    csv_data = {}
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Load work triaging CSV
        work_path = os.path.join(project_root, 'backend', 'data', 'outputs', 'work_triaging.csv')
        if os.path.exists(work_path):
            import pandas as pd
            csv_data['work_triaging'] = pd.read_csv(work_path).to_dict('records')
        
        # Load closing comments CSV
        closing_path = os.path.join(project_root, 'backend', 'data', 'outputs', 'closing_comments.csv')
        if os.path.exists(closing_path):
            csv_data['closing_comments'] = pd.read_csv(closing_path).to_dict('records')
    except Exception as e:
        print(f"Could not load CSV data for accuracy: {e}")
        csv_data = {}
    
    metrics = metrics_calculator.calculate_all_metrics(current_results)
    return jsonify(metrics)

# Old metrics calculation functions removed - using MetricsCalculator instead

# Helper functions removed - using simplified metrics instead

# Template helper functions
@app.template_filter('get_system_category')
def get_system_category(system_output):
    """Extract system category from system output."""
    if not system_output or not isinstance(system_output, dict):
        return "N/A"
    
    # Try to get category from various possible fields
    category = (system_output.get('category') or 
                system_output.get('work_intent') or 
                system_output.get('intent') or 
                "Unknown")
    
    return str(category)[:50]  # Limit length for display

@app.template_filter('get_expected_category')
def get_expected_category(result):
    """Extract expected category from result."""
    if not result or not isinstance(result, dict):
        return "N/A"
    
    # Try to get expected category from various possible fields
    expected = (result.get('expected_output', {}).get('category') or
                result.get('expected_output', {}).get('work_intent') or
                result.get('expected_output', {}).get('intent') or
                "Unknown")
    
    return str(expected)[:50]  # Limit length for display



# Voice Recording Routes
@app.route('/voice_record')
def voice_record():
    """Display voice recording interface."""
    global current_config
    
    # Provide default configuration for voice recording if none exists
    if not current_config:
        current_config = {
            'model': 'gemini-1.5-pro',  # Use specific model name
            'llm_provider': 'gemini',  # Provider name
            'temperature': 0.7,
            'test_type': 'Voice Recording',
            'voice_recording': True
        }
    
    return render_template('voice_record.html', config=current_config)

@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Process voice recording and return AI analysis (no ticket creation)."""
    global current_config
    
    # Provide default configuration for voice processing if none exists
    if not current_config:
        current_config = {
            'model': 'gemini-1.5-pro',  # Use specific model name
            'llm_provider': 'gemini',  # Provider name
            'temperature': 0.7,
            'test_type': 'Voice Recording',
            'voice_recording': True
        }
    
    try:
        # Check if audio file was uploaded
        if 'audio' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No audio file uploaded'
            })
        
        audio_file = request.files['audio']
        work_type = request.form.get('work_type', 'work_triaging')
        whisper_model = request.form.get('whisper_model', 'base')
        
        if audio_file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No audio file selected'
            })
        
        # Import voice processor
        try:
            from backend.voice.processor import create_voice_processor
        except ImportError as e:
            return jsonify({
                'success': False, 
                'error': f'Voice processing module not available: {e}. Please install dependencies first.'
            })
        
        # Create voice processor
        voice_processor = create_voice_processor(current_config)
        
        # Process uploaded audio file (but don't create tickets)
        result = voice_processor.process_audio_file(
            audio_file=audio_file,
            whisper_model=whisper_model,
            work_type=work_type
        )
        
        # Remove ticket-related fields from result
        if 'ticket' in result:
            del result['ticket']
        if 'ticket_id' in result:
            del result['ticket_id']
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Voice processing failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set_voice_config', methods=['POST'])
def set_voice_config():
    """Set configuration for voice processing."""
    global current_config
    
    try:
        data = request.get_json()
        model = data.get('model', 'gemini')
        temperature = data.get('temperature', 0.7)
        
        # Map user selection to actual model names
        if model == 'claude':
            actual_model = 'claude-3-opus-20240229'
        elif model == 'gemini':
            actual_model = 'gemini-1.5-pro'
        else:
            actual_model = model
        
        current_config = {
            'model': actual_model,  # Use the actual model name
            'llm_provider': model,  # Keep the provider name (gemini/claude)
            'temperature': temperature,
            'test_type': 'Voice Recording',
            'voice_recording': True
        }
        
        return jsonify({'success': True, 'config': current_config})
        
    except Exception as e:
        logger.error(f"Failed to set voice config: {e}")
        return jsonify({'success': False, 'error': str(e)})












if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

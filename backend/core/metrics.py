"""
Metrics calculation module for Voice Note Parser
Uses direct JSON comparison instead of CSV tables for faster, cleaner metrics
"""

from typing import Dict, List, Any, Tuple
import json
import os
from .validation import validate_work_triaging_output, validate_closing_comment_output


class MetricsCalculator:
    """Calculate metrics using direct JSON comparison - much faster and cleaner."""
    
    def __init__(self):
        self.expected_data = self._load_expected_outputs()
    
    def calculate_work_triaging_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics for Work Triaging results using direct JSON comparison."""
        if not results:
            return self._empty_wt_metrics()
        
        total_inputs = len(results)
        schema_compliant = 0
        processing_success = 0
        
        for result in results:
            # Check schema compliance
            if self._is_wt_schema_compliant(result):
                schema_compliant += 1
            
            # Check processing success
            if result.get('system_output') and isinstance(result['system_output'], dict):
                processing_success += 1
        
        # Calculate accuracy using direct JSON comparison
        accuracy_score, accuracy_breakdown = self._calculate_wt_accuracy_direct(results)
        
        # Calculate averages
        schema_compliance_rate = (schema_compliant / total_inputs) * 100 if total_inputs > 0 else 0
        processing_success_rate = (processing_success / total_inputs) * 100 if total_inputs > 0 else 0
        
        return {
            'total_inputs': total_inputs,
            'schema_compliance': round(schema_compliance_rate, 2),
            'processing_success': round(processing_success_rate, 2),
            'average_accuracy': round(accuracy_score, 2),
            'accuracy_formula': 'Category + Asset + Status + Work Type + Assignment (each 0-100%)',
            'accuracy_breakdown': accuracy_breakdown
        }
    
    def calculate_closing_comment_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics for Closing Comment results using direct JSON comparison."""
        if not results:
            return self._empty_cc_metrics()
        
        total_inputs = len(results)
        schema_compliant = 0
        processing_success = 0
        
        for result in results:
            # Check schema compliance
            if self._is_cc_schema_compliant(result):
                schema_compliant += 1
            
            # Check processing success
            if result.get('system_output') and isinstance(result['system_output'], dict):
                processing_success += 1
        
        # Calculate accuracy using direct JSON comparison
        accuracy_score, accuracy_breakdown = self._calculate_cc_accuracy_direct(results)
        
        # Calculate averages
        schema_compliance_rate = (schema_compliant / total_inputs) * 100 if total_inputs > 0 else 0
        processing_success_rate = (processing_success / total_inputs) * 100 if total_inputs > 0 else 0
        
        return {
            'total_inputs': total_inputs,
            'schema_compliance': round(schema_compliance_rate, 2),
            'processing_success': round(processing_success_rate, 2),
            'average_accuracy': round(accuracy_score, 2),
            'accuracy_formula': 'Downtime + Comment Population (each 0-100%)',
            'accuracy_breakdown': accuracy_breakdown
        }
    
    def calculate_all_metrics(self, results: Dict[str, List]) -> Dict[str, Dict]:
        """Calculate all metrics for both work triaging and closing comments."""
        # Expected structure from system_generated_outputs.json:
        # - "work_item_triaging": array of work triaging results
        # - "closing_comment": array of closing comment results
        
        work_triaging_results = results.get('work_item_triaging', [])
        closing_comment_results = results.get('closing_comment', [])
        
        return {
            'work_triaging': self.calculate_work_triaging_metrics(work_triaging_results),
            'closing_comments': self.calculate_closing_comment_metrics(closing_comment_results)
        }
    
    def _calculate_wt_accuracy_direct(self, results: List[Dict]) -> Tuple[float, Dict]:
        """Calculate Work Triaging accuracy directly from JSON comparison."""
        if not results or not self.expected_data:
            return 0.0, {}
        
        total_score = 0.0
        valid_entries = 0
        component_scores = {
            'category': {'total': 0.0, 'count': 0},
            'asset': {'total': 0.0, 'count': 0},
            'status': {'total': 0.0, 'count': 0},
            'work_type': {'total': 0.0, 'count': 0},
            'assignment': {'total': 0.0, 'count': 0}
        }
        
        for result in results:
            test_id = result.get('id')
            system_output = result.get('system_output', {})
            
            # Find expected output for this test_id
            expected_output = self._find_expected_wt_output(test_id)
            
            if expected_output:
                # Direct field comparison
                category_match = self._compare_categories(system_output, expected_output)
                asset_match = self._compare_asset_ids(system_output, expected_output)
                status_match = self._compare_status(system_output, expected_output)
                work_type_match = self._compare_work_types(system_output, expected_output)
                assignment_match = self._compare_assignments(system_output, expected_output)
                
                # Calculate scores (100 for match, 0 for mismatch)
                scores = [category_match, asset_match, status_match, work_type_match, assignment_match]
                entry_score = sum(scores) / len(scores) * 100
                
                total_score += entry_score
                valid_entries += 1
                
                # Update component scores
                component_scores['category']['total'] += scores[0] * 100
                component_scores['category']['count'] += 1
                component_scores['asset']['total'] += scores[1] * 100
                component_scores['asset']['count'] += 1
                component_scores['status']['total'] += scores[2] * 100
                component_scores['status']['count'] += 1
                component_scores['work_type']['total'] += scores[3] * 100
                component_scores['work_type']['count'] += 1
                component_scores['assignment']['total'] += scores[4] * 100
                component_scores['assignment']['count'] += 1
        
        # Calculate final scores
        final_score = (total_score / valid_entries) if valid_entries > 0 else 0.0
        
        # Calculate component averages
        for component in component_scores.values():
            if component['count'] > 0:
                component['average'] = component['total'] / component['count']
            else:
                component['average'] = 0.0
        
        return final_score, component_scores
    
    def _calculate_cc_accuracy_direct(self, results: List[Dict]) -> Tuple[float, Dict]:
        """Calculate Closing Comment accuracy directly from JSON comparison."""
        if not results or not self.expected_data:
            return 0.0, {}
        
        total_score = 0.0
        valid_entries = 0
        component_scores = {
            'downtime': {'total': 0.0, 'count': 0},
            'comment_population': {'total': 0.0, 'count': 0}
        }
        
        for result in results:
            test_id = result.get('id')
            system_output = result.get('system_output', {})
            
            # Find expected output for this test_id
            expected_output = self._find_expected_cc_output(test_id)
            
            if expected_output:
                # Direct field comparison
                downtime_match = self._compare_downtime(system_output, expected_output)
                comment_match = self._compare_comments(system_output, expected_output)
                
                # Calculate scores (100 for match, 0 for mismatch)
                scores = [downtime_match, comment_match]
                entry_score = sum(scores) / len(scores) * 100
                
                total_score += entry_score
                valid_entries += 1
                
                # Update component scores
                component_scores['downtime']['total'] += scores[0] * 100
                component_scores['downtime']['count'] += 1
                component_scores['comment_population']['total'] += scores[1] * 100
                component_scores['comment_population']['count'] += 1
        
        # Calculate final scores
        final_score = (total_score / valid_entries) if valid_entries > 0 else 0.0
        
        # Calculate component averages
        for component in component_scores.values():
            if component['count'] > 0:
                component['average'] = component['total'] / component['count']
            else:
                component['average'] = 0.0
        
        return final_score, component_scores
    
    def _load_expected_outputs(self) -> Dict:
        """Load expected outputs from Attachment B JSON file."""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            expected_file = os.path.join(project_root, 'dataset', 'Thunderbird-Take-Home-Attachment-B.json')
            
            with open(expected_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load expected outputs: {e}")
            return {}
    
    def _find_expected_wt_output(self, test_id: str) -> Dict:
        """Find expected work triaging output for a given test_id."""
        if 'work_item_triaging' in self.expected_data:
            for exp in self.expected_data['work_item_triaging']:
                if exp.get('id') == test_id:
                    return exp.get('expected_output', {})
        return {}
    
    def _find_expected_cc_output(self, test_id: str) -> Dict:
        """Find expected closing comment output for a given test_id."""
        if 'closing_comment' in self.expected_data:
            for exp in self.expected_data['closing_comment']:
                if exp.get('id') == test_id:
                    return exp.get('expected_output', {})
        return {}
    
    def _compare_categories(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare work item categories between system and expected output."""
        system_category = self._extract_category(system_output)
        expected_category = self._extract_category(expected_output)
        return system_category == expected_category
    
    def _compare_asset_ids(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare asset IDs between system and expected output."""
        system_asset = self._extract_asset_id(system_output)
        expected_asset = self._extract_asset_id(expected_output)
        return system_asset == expected_asset
    
    def _compare_status(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare status between system and expected output."""
        system_status = self._extract_status(system_output)
        expected_status = self._extract_status(expected_output)
        return system_status == expected_status
    
    def _compare_work_types(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare work type IDs between system and expected output."""
        system_work_type = self._extract_work_type_id(system_output)
        expected_work_type = self._extract_work_type_id(expected_output)
        return system_work_type == expected_work_type
    
    def _compare_assignments(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare assigned_to between system and expected output."""
        system_assigned = self._extract_assigned_to(system_output)
        expected_assigned = self._extract_assigned_to(expected_output)
        return system_assigned == expected_assigned
    
    def _compare_downtime(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare downtime hours between system and expected output."""
        system_downtime = system_output.get('actual_downtime_hours')
        expected_downtime = expected_output.get('actual_downtime_hours')
        
        # Handle null/None values
        if system_downtime is None and expected_downtime is None:
            return True  # Both null means they match
        
        if system_downtime is None or expected_downtime is None:
            return False  # One is null, other isn't - they don't match
        
        # Both are numeric values, compare them
        try:
            system_val = float(system_downtime)
            expected_val = float(expected_downtime)
            return abs(system_val - expected_val) < 0.01  # Allow small floating point differences
        except (ValueError, TypeError):
            return False  # Invalid numeric values
    
    def _compare_comments(self, system_output: Dict, expected_output: Dict) -> bool:
        """Compare closing comments between system and expected output."""
        system_comment = system_output.get('closing_comment', '')
        expected_comment = expected_output.get('closing_comment', '')
        return bool(system_comment and expected_comment)  # Both should have content
    
    def _extract_category(self, output: Dict) -> str:
        """Extract category from output structure."""
        if output.get('work_requests'):
            return 'work_request'
        elif output.get('work_orders'):
            return 'work_order'
        elif output.get('inspection_tasks'):
            return 'inspection_task'
        elif output.get('general_tasks'):
            return 'general_task'
        return 'unknown'
    
    def _extract_asset_id(self, output: Dict) -> str:
        """Extract asset ID from output structure."""
        for key in ['work_requests', 'work_orders', 'inspection_tasks', 'general_tasks']:
            if output.get(key) and len(output[key]) > 0:
                return output[key][0].get('asset_id', '')
        return ''
    
    def _extract_status(self, output: Dict) -> str:
        """Extract status from output structure."""
        for key in ['work_requests', 'work_orders', 'inspection_tasks', 'general_tasks']:
            if output.get(key) and len(output[key]) > 0:
                return output[key][0].get('status', '')
        return ''
    
    def _extract_work_type_id(self, output: Dict) -> str:
        """Extract work type ID from output structure."""
        for key in ['work_requests', 'work_orders', 'inspection_tasks', 'general_tasks']:
            if output.get(key) and len(output[key]) > 0:
                return output[key][0].get('work_type_id', '')
        return ''
    
    def _extract_assigned_to(self, output: Dict) -> str:
        """Extract assigned_to from output structure."""
        for key in ['work_requests', 'work_orders', 'inspection_tasks', 'general_tasks']:
            if output.get(key) and len(output[key]) > 0:
                return output[key][0].get('assigned_to', '')
        return ''
    
    def _is_wt_schema_compliant(self, result: Dict) -> bool:
        """Check if Work Triaging result is schema compliant."""
        try:
            if 'system_output' not in result:
                return False
            return validate_work_triaging_output(result['system_output'], result.get('id', 'unknown'))
        except Exception:
            return False
    
    def _is_cc_schema_compliant(self, result: Dict) -> bool:
        """Check if Closing Comment result is schema compliant."""
        try:
            if 'system_output' not in result:
                return False
            return validate_closing_comment_output(result['system_output'], result.get('id', 'unknown'))
        except Exception:
            return False
    
    def _empty_wt_metrics(self) -> Dict[str, Any]:
        """Return empty work triaging metrics."""
        return {
            'total_inputs': 0,
            'schema_compliance': 0.0,
            'processing_success': 0.0,
            'average_accuracy': 0.0,
            'accuracy_formula': 'Category + Asset + Status + Work Type + Assignment (each 0-100%)',
            'accuracy_breakdown': {}
        }
    
    def _empty_cc_metrics(self) -> Dict[str, Any]:
        """Return empty closing comment metrics."""
        return {
            'total_inputs': 0,
            'schema_compliance': 0.0,
            'processing_success': 0.0,
            'average_accuracy': 0.0,
            'accuracy_formula': 'Downtime + Comment Population (each 0-100%)',
            'accuracy_breakdown': {}
        }

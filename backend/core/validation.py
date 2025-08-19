#!/usr/bin/env python3
"""
Pydantic Schema Validation for Maintenance Voice Note Parser

This module provides proper JSON schema validation using Pydantic for:
1. Work Item Triaging outputs
2. Closing Comment outputs

The schemas exactly match Attachment B structure with 'system_output' instead of 'expected_output'.

Author: AI Assistant
Version: 2.0
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
import logging


class WorkRequest(BaseModel):
    """Schema for individual work request items."""
    title: str = Field(..., description="Descriptive title of the work request")
    description: str = Field(..., description="Detailed description of the work needed")
    status: str = Field(..., description="Current status (pending, in_progress, completed, etc.)")
    asset_id: Optional[str] = Field(None, description="Asset identifier if applicable")
    work_type_id: Optional[str] = Field(None, description="Work type identifier if applicable")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the work")


class WorkOrder(BaseModel):
    """Schema for individual work order items."""
    title: str = Field(..., description="Descriptive title of the work order")
    description: str = Field(..., description="Detailed description of the work")
    status: str = Field(..., description="Current status (draft, approved, in_progress, completed)")
    asset_id: Optional[str] = Field(None, description="Asset identifier if applicable")
    work_type_id: Optional[str] = Field(None, description="Work type identifier if applicable")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the work")
    comment: Optional[str] = Field(None, description="Additional comments or context")
    user_query: Optional[str] = Field(None, description="Original user query if preserved")


class InspectionTask(BaseModel):
    """Schema for individual inspection task items."""
    title: str = Field(..., description="Descriptive title of the inspection task")
    description: str = Field(..., description="Detailed description of the inspection needed")
    status: str = Field(..., description="Current status (pending, in_progress, completed)")
    asset_id: Optional[str] = Field(None, description="Asset identifier if applicable")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the inspection")


class GeneralTask(BaseModel):
    """Schema for individual general task items."""
    title: str = Field(..., description="Descriptive title of the general task")
    description: str = Field(..., description="Detailed description of the task")
    status: str = Field(..., description="Current status (pending, in_progress, completed)")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the task")


class WorkItemTriagingOutput(BaseModel):
    """Schema for work item triaging output."""
    work_requests: List[WorkRequest] = Field(default_factory=list, description="List of work requests")
    work_orders: List[WorkOrder] = Field(default_factory=list, description="List of work orders")
    inspection_tasks: List[InspectionTask] = Field(default_factory=list, description="List of inspection tasks")
    general_tasks: List[GeneralTask] = Field(default_factory=list, description="List of general tasks")


class ClosingCommentOutput(BaseModel):
    """Schema for closing comment output."""
    closing_comment: str = Field(..., description="Generated closing comment text")
    actual_downtime_hours: Optional[float] = Field(None, description="Actual equipment downtime in hours")


# New schemas matching Attachment B structure exactly
class WorkItemTriagingEntry(BaseModel):
    """Schema for individual work item triaging entry matching Attachment B."""
    id: str = Field(..., description="Test identifier (e.g., wt_001)")
    input: str = Field(..., description="Input voice transcription text")
    system_output: WorkItemTriagingOutput = Field(..., description="AI-generated output")
    test_focus: str = Field(..., description="Test focus description")


class ClosingCommentEntry(BaseModel):
    """Schema for individual closing comment entry matching Attachment B."""
    id: str = Field(..., description="Test identifier (e.g., cc_001)")
    input: str = Field(..., description="Input voice transcription text")
    system_output: ClosingCommentOutput = Field(..., description="AI-generated output")
    test_focus: str = Field(..., description="Test focus description")


class SystemGeneratedOutputs(BaseModel):
    """Schema for the complete system output matching Attachment B structure."""
    work_item_triaging: List[WorkItemTriagingEntry] = Field(..., description="Work triaging results")
    closing_comment: List[ClosingCommentEntry] = Field(..., description="Closing comment results")


def validate_work_triaging_output(data: dict, test_id: str) -> bool:
    """
    Validate work triaging output against Pydantic schema.
    
    Args:
        data: Output data to validate
        test_id: Test identifier for tracking
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate against schema
        validated_data = WorkItemTriagingOutput(**data)
        return True
    except Exception as e:
        logging.error(f"Schema validation failed for {test_id}: {str(e)}")
        return False


def validate_closing_comment_output(data: dict, test_id: str) -> bool:
    """
    Validate closing comment output against Pydantic schema.
    
    Args:
        data: Output data to validate
        test_id: Test identifier for tracking
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate against schema
        validated_data = ClosingCommentOutput(**data)
        return True
    except Exception as e:
        logging.error(f"Schema validation failed for {test_id}: {str(e)}")
        return False


def validate_complete_output(data: dict) -> bool:
    """
    Validate the complete system output against Attachment B structure.
    
    Args:
        data: Complete output data to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate against complete schema
        validated_data = SystemGeneratedOutputs(**data)
        return True
    except Exception as e:
        logging.error(f"Complete schema validation failed: {str(e)}")
        return False


def validate_output(data: dict, output_type: str, test_id: str) -> bool:
    """
    Main validation function that routes to appropriate validator.
    
    Args:
        data: Output data to validate
        output_type: Type of output ('work_triaging' or 'closing_comment')
        test_id: Test identifier for tracking
        
    Returns:
        True if valid, False otherwise
    """
    if output_type == 'work_triaging':
        return validate_work_triaging_output(data, test_id)
    elif output_type == 'closing_comment':
        return validate_closing_comment_output(data, test_id)
    else:
        logging.error(f"Unknown output type: {output_type}")
        return False

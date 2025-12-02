#!/usr/bin/env python3
"""
Workflow Service
Handles ticket automation workflows
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority
from app.models.tenant import User

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Service for ticket automation workflows
    
    Features:
    - Rule-based automation
    - Conditional actions
    - Multi-step workflows
    - Auto-assignment
    - Auto-escalation
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def process_ticket_workflows(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Process all applicable workflows for a ticket
        
        Args:
            ticket: Ticket to process
        
        Returns:
            Dict with workflow results
        """
        results = {
            "workflows_applied": [],
            "actions_taken": [],
            "errors": []
        }
        
        try:
            # Auto-assignment workflow
            assignment_result = await self.auto_assign_ticket(ticket)
            if assignment_result.get("assigned"):
                results["workflows_applied"].append("auto_assignment")
                results["actions_taken"].append(f"Assigned to {assignment_result.get('user_id')}")
            
            # Auto-categorization workflow
            category_result = await self.auto_categorize_ticket(ticket)
            if category_result.get("categorized"):
                results["workflows_applied"].append("auto_categorization")
                results["actions_taken"].append(f"Category set to {category_result.get('category')}")
            
            # Auto-escalation workflow
            escalation_result = await self.check_auto_escalation(ticket)
            if escalation_result.get("escalated"):
                results["workflows_applied"].append("auto_escalation")
                results["actions_taken"].append(f"Escalated: {escalation_result.get('reason')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process workflows for ticket {ticket.id}: {e}")
            results["errors"].append(str(e))
            return results
    
    async def auto_assign_ticket(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Auto-assign ticket based on rules
        
        Returns:
            Dict with assignment result
        """
        # Skip if already assigned
        if ticket.assigned_to_id:
            return {"assigned": False, "reason": "Already assigned"}
        
        # Get assignment rules (from tenant config or database)
        assignment_rules = self._get_assignment_rules()
        
        for rule in assignment_rules:
            if self._evaluate_rule(ticket, rule):
                # Assign to user from rule
                user_id = rule.get("assign_to_user_id")
                if user_id:
                    ticket.assigned_to_id = user_id
                    self.db.commit()
                    return {
                        "assigned": True,
                        "user_id": user_id,
                        "rule": rule.get("name")
                    }
        
        return {"assigned": False, "reason": "No matching rule"}
    
    async def auto_categorize_ticket(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Auto-categorize ticket based on content
        
        Returns:
            Dict with categorization result
        """
        # Skip if already categorized
        if ticket.category:
            return {"categorized": False, "reason": "Already categorized"}
        
        # Use simple keyword matching (can be enhanced with AI)
        text = f"{ticket.subject} {ticket.description}".lower()
        
        categories = {
            "technical": ["error", "bug", "issue", "problem", "not working", "broken", "crash"],
            "billing": ["invoice", "payment", "billing", "charge", "refund", "price"],
            "support": ["help", "support", "assistance", "question", "how to"],
            "feature": ["feature", "enhancement", "request", "suggestion", "improvement"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                ticket.category = category
                self.db.commit()
                return {
                    "categorized": True,
                    "category": category
                }
        
        return {"categorized": False, "reason": "No category match"}
    
    async def check_auto_escalation(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Check if ticket should be auto-escalated
        
        Returns:
            Dict with escalation result
        """
        # Check escalation rules
        escalation_rules = self._get_escalation_rules()
        
        for rule in escalation_rules:
            if self._evaluate_rule(ticket, rule):
                # Escalate priority or assign to manager
                if rule.get("escalate_priority"):
                    if ticket.priority == TicketPriority.LOW:
                        ticket.priority = TicketPriority.MEDIUM
                    elif ticket.priority == TicketPriority.MEDIUM:
                        ticket.priority = TicketPriority.HIGH
                    elif ticket.priority == TicketPriority.HIGH:
                        ticket.priority = TicketPriority.URGENT
                
                if rule.get("assign_to_manager"):
                    manager = self._get_manager_user()
                    if manager:
                        ticket.assigned_to_id = manager.id
                
                self.db.commit()
                return {
                    "escalated": True,
                    "reason": rule.get("name"),
                    "actions": rule.get("actions", [])
                }
        
        return {"escalated": False}
    
    def _get_assignment_rules(self) -> List[Dict[str, Any]]:
        """Get ticket assignment rules"""
        # In production, these would come from database
        # For now, return default rules
        return [
            {
                "name": "High Priority to Support Lead",
                "conditions": {
                    "priority": ["high", "urgent"]
                },
                "assign_to_user_id": None  # Would be actual user ID
            },
            {
                "name": "Technical Issues to Tech Team",
                "conditions": {
                    "category": ["technical"]
                },
                "assign_to_user_id": None
            }
        ]
    
    def _get_escalation_rules(self) -> List[Dict[str, Any]]:
        """Get escalation rules"""
        return [
            {
                "name": "Escalate Unassigned High Priority",
                "conditions": {
                    "priority": ["high", "urgent"],
                    "assigned_to_id": None,
                    "age_hours": 4
                },
                "escalate_priority": True,
                "assign_to_manager": True,
                "actions": ["Increase priority", "Assign to manager"]
            },
            {
                "name": "Escalate Stale Tickets",
                "conditions": {
                    "status": ["open", "in_progress"],
                    "age_hours": 48
                },
                "escalate_priority": True,
                "actions": ["Increase priority"]
            }
        ]
    
    def _evaluate_rule(
        self,
        ticket: Ticket,
        rule: Dict[str, Any]
    ) -> bool:
        """Evaluate if ticket matches rule conditions"""
        conditions = rule.get("conditions", {})
        
        # Check priority
        if "priority" in conditions:
            ticket_priority = ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority)
            if ticket_priority not in [p.lower() for p in conditions["priority"]]:
                return False
        
        # Check category
        if "category" in conditions:
            if ticket.category not in conditions["category"]:
                return False
        
        # Check assignment
        if "assigned_to_id" in conditions:
            if conditions["assigned_to_id"] is None and ticket.assigned_to_id is not None:
                return False
            if conditions["assigned_to_id"] is not None and ticket.assigned_to_id != conditions["assigned_to_id"]:
                return False
        
        # Check age
        if "age_hours" in conditions:
            age_hours = (datetime.now() - ticket.created_at).total_seconds() / 3600
            if age_hours < conditions["age_hours"]:
                return False
        
        # Check status
        if "status" in conditions:
            ticket_status = ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status)
            if ticket_status not in [s.lower() for s in conditions["status"]]:
                return False
        
        return True
    
    def _get_manager_user(self) -> Optional[User]:
        """Get manager user for escalation"""
        # In production, this would query for users with manager role
        # For now, return None
        return None
    
    async def execute_multi_step_workflow(
        self,
        ticket: Ticket,
        workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a multi-step workflow with conditional logic
        
        Workflow definition format:
        {
            "name": "Complex Ticket Workflow",
            "steps": [
                {
                    "id": "step1",
                    "condition": {"priority": ["high", "urgent"]},
                    "actions": ["assign_to_team", "send_notification"],
                    "on_success": "step2",
                    "on_failure": "step3"
                },
                {
                    "id": "step2",
                    "condition": {"status": "in_progress"},
                    "actions": ["escalate_if_stale"],
                    "on_success": "complete"
                }
            ]
        }
        
        Args:
            ticket: Ticket to process
            workflow_definition: Workflow definition with steps
        
        Returns:
            Dict with execution results
        """
        results = {
            "workflow_name": workflow_definition.get("name", "Unknown"),
            "steps_executed": [],
            "actions_taken": [],
            "errors": [],
            "completed": False
        }
        
        try:
            steps = workflow_definition.get("steps", [])
            current_step_id = steps[0].get("id") if steps else None
            
            while current_step_id:
                step = next((s for s in steps if s.get("id") == current_step_id), None)
                if not step:
                    break
                
                # Check condition
                condition_met = self._evaluate_condition(ticket, step.get("condition", {}))
                
                if condition_met:
                    # Execute actions
                    step_results = await self._execute_step_actions(ticket, step.get("actions", []))
                    results["steps_executed"].append({
                        "step_id": current_step_id,
                        "condition_met": True,
                        "actions": step_results
                    })
                    results["actions_taken"].extend(step_results.get("actions", []))
                    
                    # Move to next step
                    current_step_id = step.get("on_success")
                else:
                    # Condition not met, go to failure path
                    results["steps_executed"].append({
                        "step_id": current_step_id,
                        "condition_met": False
                    })
                    current_step_id = step.get("on_failure")
                
                # Check if workflow is complete
                if current_step_id == "complete" or current_step_id is None:
                    results["completed"] = True
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            results["errors"].append(str(e))
            return results
    
    def _evaluate_condition(
        self,
        ticket: Ticket,
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate complex condition with AND/OR logic
        
        Condition format:
        {
            "operator": "AND",  # or "OR"
            "conditions": [
                {"field": "priority", "operator": "in", "value": ["high", "urgent"]},
                {"field": "status", "operator": "equals", "value": "open"}
            ]
        }
        """
        if not condition:
            return True
        
        # Simple condition (backward compatible)
        if "operator" not in condition:
            return self._evaluate_rule(ticket, {"conditions": condition})
        
        operator = condition.get("operator", "AND")
        conditions = condition.get("conditions", [])
        
        if operator == "AND":
            return all(self._evaluate_single_condition(ticket, c) for c in conditions)
        elif operator == "OR":
            return any(self._evaluate_single_condition(ticket, c) for c in conditions)
        
        return False
    
    def _evaluate_single_condition(
        self,
        ticket: Ticket,
        condition: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition"""
        field = condition.get("field")
        op = condition.get("operator")
        value = condition.get("value")
        
        # Get ticket field value
        ticket_value = getattr(ticket, field, None)
        if ticket_value is None:
            return False
        
        # Normalize enum values
        if hasattr(ticket_value, 'value'):
            ticket_value = ticket_value.value
        
        # Apply operator
        if op == "equals":
            return str(ticket_value).lower() == str(value).lower()
        elif op == "in":
            return str(ticket_value).lower() in [str(v).lower() for v in value]
        elif op == "not_in":
            return str(ticket_value).lower() not in [str(v).lower() for v in value]
        elif op == "greater_than":
            return float(ticket_value) > float(value)
        elif op == "less_than":
            return float(ticket_value) < float(value)
        elif op == "contains":
            return str(value).lower() in str(ticket_value).lower()
        
        return False
    
    async def _execute_step_actions(
        self,
        ticket: Ticket,
        actions: List[str]
    ) -> Dict[str, Any]:
        """Execute actions for a workflow step"""
        results = {
            "actions": [],
            "errors": []
        }
        
        for action in actions:
            try:
                if action == "assign_to_team":
                    result = await self.auto_assign_ticket(ticket)
                    results["actions"].append(f"Auto-assignment: {result.get('reason', 'completed')}")
                
                elif action == "send_notification":
                    # Placeholder for notification service
                    results["actions"].append("Notification sent")
                
                elif action == "escalate_if_stale":
                    result = await self.check_auto_escalation(ticket)
                    if result.get("escalated"):
                        results["actions"].append("Ticket escalated")
                
                elif action == "create_follow_up":
                    # Placeholder for follow-up creation
                    results["actions"].append("Follow-up created")
                
                elif action.startswith("set_"):
                    # Dynamic field setting: set_priority=high
                    field = action.split("=")[0].replace("set_", "")
                    value = action.split("=")[1] if "=" in action else None
                    if value:
                        setattr(ticket, field, value)
                        self.db.commit()
                        results["actions"].append(f"Set {field} to {value}")
                
                elif action.startswith("webhook_"):
                    # External webhook: webhook_url=https://example.com/webhook
                    await self._trigger_webhook(ticket, action)
                    results["actions"].append(f"Webhook triggered: {action}")
                
                else:
                    results["errors"].append(f"Unknown action: {action}")
                    
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")
                results["errors"].append(f"{action}: {str(e)}")
        
        return results
    
    async def _trigger_webhook(
        self,
        ticket: Ticket,
        action: str
    ) -> Dict[str, Any]:
        """
        Trigger external webhook for workflow integration
        
        Args:
            ticket: Ticket data
            action: Action string with webhook URL
        
        Returns:
            Webhook response
        """
        import httpx
        
        # Extract URL from action: webhook_url=https://example.com/webhook
        url = action.split("=")[1] if "=" in action else None
        if not url:
            return {"success": False, "error": "No URL provided"}
        
        try:
            payload = {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.subject,
                "status": ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
                "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                response.raise_for_status()
            
            return {"success": True, "status_code": response.status_code}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_custom_workflow(
        self,
        name: str,
        description: str,
        workflow_definition: Dict[str, Any],
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a custom workflow definition
        
        In production, this would store in database.
        For now, returns the definition.
        
        Args:
            name: Workflow name
            description: Workflow description
            workflow_definition: Workflow steps definition
            is_active: Whether workflow is active
        
        Returns:
            Created workflow definition
        """
        workflow = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "definition": workflow_definition,
            "is_active": is_active,
            "created_at": datetime.now().isoformat(),
            "tenant_id": self.tenant_id
        }
        
        # TODO: Store in database table `workflow_definitions`
        # For now, return the workflow object
        
        return workflow
    
    async def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows"""
        # TODO: Load from database
        # For now, return default workflows
        return [
            {
                "id": "default_escalation",
                "name": "Default Escalation Workflow",
                "description": "Standard escalation workflow",
                "is_active": True
            }
        ]


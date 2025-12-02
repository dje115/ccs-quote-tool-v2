#!/usr/bin/env python3
"""
SLA Intelligence Service

Provides SLA monitoring and risk assessment:
- Auto-assign ticket type, priority, and SLA breach risk
- SLA timer tracking
- Risk indicators
- Auto-response/close for low-complexity tickets
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.helpdesk import Ticket, TicketStatus, TicketPriority, TicketType, SLAPolicy
from app.models.tenant import User

logger = logging.getLogger(__name__)


class SLAIntelligenceService:
    """
    Service for SLA monitoring and intelligence
    
    Features:
    - Auto-assign ticket type, priority, SLA breach risk
    - SLA timer tracking
    - Risk indicators
    - Auto-response/close for low-complexity tickets
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def assess_sla_risk(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Assess SLA breach risk for ticket
        
        Returns:
            Dict with:
            - risk_level: "low", "medium", "high", "critical"
            - time_remaining_hours: Hours until SLA breach
            - breach_probability: Probability of breach (0.0-1.0)
            - recommended_actions: List of recommended actions
        """
        # Get SLA policy for ticket
        sla_policy = await self._get_sla_policy(ticket)
        
        if not sla_policy:
            return {
                "risk_level": "low",
                "time_remaining_hours": None,
                "breach_probability": 0.0,
                "recommended_actions": []
            }
        
        # Calculate time remaining
        target_hours = sla_policy.resolution_hours or sla_policy.first_response_hours or 24
        time_elapsed = (datetime.now(timezone.utc) - ticket.created_at).total_seconds() / 3600
        time_remaining_hours = target_hours - time_elapsed
        
        # Calculate breach probability based on:
        # - Time remaining
        # - Ticket priority
        # - Ticket status
        # - Assigned agent availability
        
        breach_probability = self._calculate_breach_probability(
            time_remaining_hours,
            ticket.priority,
            ticket.status,
            ticket.assigned_to_id is not None
        )
        
        # Determine risk level
        if breach_probability >= 0.8:
            risk_level = "critical"
        elif breach_probability >= 0.6:
            risk_level = "high"
        elif breach_probability >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            risk_level,
            time_remaining_hours,
            ticket
        )
        
        return {
            "risk_level": risk_level,
            "time_remaining_hours": max(0, time_remaining_hours),
            "breach_probability": breach_probability,
            "recommended_actions": recommended_actions,
            "sla_target_hours": target_hours,
            "time_elapsed_hours": time_elapsed
        }
    
    async def _get_sla_policy(self, ticket: Ticket) -> Optional[SLAPolicy]:
        """Get applicable SLA policy for ticket"""
        # Query SLA policies matching ticket criteria
        stmt = select(SLAPolicy).where(
            and_(
                SLAPolicy.tenant_id == self.tenant_id,
                SLAPolicy.is_active == True
            )
        )
        
        # Try to find policy matching priority and type
        policies = self.db.execute(stmt).scalars().all()
        
        for policy in policies:
            # Check if policy matches ticket priority
            if policy.priority and policy.priority != ticket.priority:
                continue
            
            # Check if policy matches ticket type
            if policy.ticket_type and policy.ticket_type != ticket.ticket_type:
                continue
            
            # Check if policy applies to specific customers
            if policy.customer_ids:
                if ticket.customer_id not in policy.customer_ids:
                    continue
            
            return policy
        
        # Return first active policy as default
        if policies:
            return policies[0]
        
        return None
    
    def _calculate_breach_probability(
        self,
        time_remaining_hours: float,
        priority: TicketPriority,
        status: TicketStatus,
        is_assigned: bool
    ) -> float:
        """
        Calculate probability of SLA breach
        
        Returns:
            Probability between 0.0 and 1.0
        """
        probability = 0.0
        
        # Base probability from time remaining
        if time_remaining_hours <= 0:
            probability = 1.0  # Already breached
        elif time_remaining_hours < 1:
            probability = 0.9  # Less than 1 hour remaining
        elif time_remaining_hours < 4:
            probability = 0.7  # Less than 4 hours remaining
        elif time_remaining_hours < 8:
            probability = 0.5  # Less than 8 hours remaining
        elif time_remaining_hours < 24:
            probability = 0.3  # Less than 24 hours remaining
        else:
            probability = 0.1  # More than 24 hours remaining
        
        # Adjust based on priority
        if priority == TicketPriority.URGENT:
            probability += 0.2
        elif priority == TicketPriority.HIGH:
            probability += 0.1
        elif priority == TicketPriority.LOW:
            probability -= 0.1
        
        # Adjust based on status
        if status == TicketStatus.OPEN and not is_assigned:
            probability += 0.2  # Unassigned open tickets are higher risk
        elif status == TicketStatus.WAITING_CUSTOMER:
            probability -= 0.1  # Waiting on customer reduces risk
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, probability))
    
    def _generate_recommended_actions(
        self,
        risk_level: str,
        time_remaining_hours: float,
        ticket: Ticket
    ) -> List[str]:
        """Generate recommended actions based on risk level"""
        actions = []
        
        if risk_level == "critical":
            actions.append("⚠️ CRITICAL: SLA breach imminent - escalate immediately")
            if not ticket.assigned_to_id:
                actions.append("Assign ticket to available agent immediately")
            actions.append("Notify manager and customer of potential delay")
            actions.append("Consider temporary workaround or partial resolution")
        
        elif risk_level == "high":
            actions.append("⚠️ HIGH RISK: Monitor closely - escalate if no progress")
            if not ticket.assigned_to_id:
                actions.append("Assign ticket to specialist")
            actions.append("Set reminder to check progress in 2 hours")
        
        elif risk_level == "medium":
            actions.append("Monitor ticket progress")
            if not ticket.assigned_to_id:
                actions.append("Consider assigning ticket")
        
        else:
            actions.append("Ticket is on track - continue monitoring")
        
        # Add time-specific actions
        if time_remaining_hours and time_remaining_hours < 4:
            actions.append(f"⏰ Only {time_remaining_hours:.1f} hours remaining until SLA target")
        
        return actions
    
    async def auto_assign_ticket(
        self,
        ticket: Ticket
    ) -> Optional[str]:
        """
        Auto-assign ticket to appropriate agent
        
        Returns:
            User ID of assigned agent or None
        """
        # TODO: Implement intelligent auto-assignment based on:
        # - Agent workload
        # - Agent skills/expertise
        # - Ticket type/priority
        # - Agent availability
        
        # For now, return None (no auto-assignment)
        return None
    
    async def should_auto_close(
        self,
        ticket: Ticket,
        ai_confidence: float = 0.0
    ) -> bool:
        """
        Determine if ticket should be auto-closed
        
        Args:
            ticket: Ticket object
            ai_confidence: AI confidence score (0.0-1.0)
        
        Returns:
            True if ticket should be auto-closed
        """
        # Only auto-close if:
        # - Low complexity (low priority, simple type)
        # - High AI confidence (>0.8)
        # - No customer interaction needed
        # - Not assigned to specific agent
        
        if ticket.priority != TicketPriority.LOW:
            return False
        
        if ai_confidence < 0.8:
            return False
        
        if ticket.status == TicketStatus.WAITING_CUSTOMER:
            return False
        
        if ticket.assigned_to_id:
            return False
        
        # Check if ticket has been resolved
        if ticket.status == TicketStatus.RESOLVED:
            return True
        
        return False
    
    async def get_sla_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get SLA metrics for tenant
        
        Returns:
            Dict with SLA statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Query tickets in date range
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        )
        
        tickets = self.db.execute(stmt).scalars().all()
        
        total_tickets = len(tickets)
        breached_tickets = 0
        on_time_tickets = 0
        
        for ticket in tickets:
            sla_assessment = await self.assess_sla_risk(ticket)
            
            if sla_assessment["time_remaining_hours"] is not None:
                if sla_assessment["time_remaining_hours"] <= 0:
                    breached_tickets += 1
                else:
                    on_time_tickets += 1
        
        breach_rate = (breached_tickets / total_tickets * 100) if total_tickets > 0 else 0
        
        return {
            "total_tickets": total_tickets,
            "breached_tickets": breached_tickets,
            "on_time_tickets": on_time_tickets,
            "breach_rate_percent": breach_rate,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def monitor_sla_compliance(
        self,
        ticket_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Real-time SLA monitoring for tickets
        
        Args:
            ticket_ids: Optional list of ticket IDs to monitor (all if None)
        
        Returns:
            Dict with monitoring results
        """
        if ticket_ids:
            stmt = select(Ticket).where(
                and_(
                    Ticket.tenant_id == self.tenant_id,
                    Ticket.id.in_(ticket_ids),
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                )
            )
        else:
            stmt = select(Ticket).where(
                and_(
                    Ticket.tenant_id == self.tenant_id,
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                )
            )
        
        tickets = self.db.execute(stmt).scalars().all()
        
        monitoring_results = []
        critical_count = 0
        high_count = 0
        medium_count = 0
        
        for ticket in tickets:
            assessment = await self.assess_sla_risk(ticket)
            
            if assessment["risk_level"] == "critical":
                critical_count += 1
            elif assessment["risk_level"] == "high":
                high_count += 1
            elif assessment["risk_level"] == "medium":
                medium_count += 1
            
            monitoring_results.append({
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "risk_level": assessment["risk_level"],
                "time_remaining_hours": assessment["time_remaining_hours"],
                "breach_probability": assessment["breach_probability"],
                "recommended_actions": assessment["recommended_actions"]
            })
        
        return {
            "total_monitored": len(tickets),
            "critical_risk": critical_count,
            "high_risk": high_count,
            "medium_risk": medium_count,
            "low_risk": len(tickets) - critical_count - high_count - medium_count,
            "tickets": monitoring_results
        }
    
    async def predict_breach_risk(
        self,
        ticket: Ticket,
        hours_ahead: int = 24
    ) -> Dict[str, Any]:
        """
        Predict SLA breach risk for future time periods
        
        Args:
            ticket: Ticket to analyze
            hours_ahead: Hours into future to predict
        
        Returns:
            Dict with predictions
        """
        assessment = await self.assess_sla_risk(ticket)
        
        # Predict based on current trajectory
        time_remaining = assessment.get("time_remaining_hours", 0)
        
        # Calculate predicted breach time
        if time_remaining and time_remaining > 0:
            predicted_breach_in_hours = time_remaining
        else:
            predicted_breach_in_hours = 0
        
        # Predict probability at different time points
        predictions = []
        for hour in range(0, hours_ahead + 1, 4):  # Every 4 hours
            future_time_remaining = time_remaining - hour if time_remaining else None
            if future_time_remaining is not None:
                future_probability = self._calculate_breach_probability(
                    future_time_remaining,
                    ticket.priority,
                    ticket.status,
                    ticket.assigned_to_id is not None
                )
                predictions.append({
                    "hours_from_now": hour,
                    "predicted_breach_probability": future_probability,
                    "time_remaining_hours": max(0, future_time_remaining)
                })
        
        return {
            "current_assessment": assessment,
            "predicted_breach_in_hours": predicted_breach_in_hours,
            "will_breach_within_24h": predicted_breach_in_hours <= 24 and predicted_breach_in_hours > 0,
            "predictions": predictions
        }
    
    async def get_sla_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"  # "day", "week", "month"
    ) -> Dict[str, Any]:
        """
        Get comprehensive SLA analytics
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            group_by: Grouping period
        
        Returns:
            Dict with analytics data
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Get metrics
        metrics = await self.get_sla_metrics(start_date, end_date)
        
        # Get tickets for detailed analysis
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        )
        tickets = self.db.execute(stmt).scalars().all()
        
        # Group by period
        grouped_data = {}
        for ticket in tickets:
            # Determine period key based on group_by
            if group_by == "day":
                period_key = ticket.created_at.date().isoformat()
            elif group_by == "week":
                week_start = ticket.created_at - timedelta(days=ticket.created_at.weekday())
                period_key = week_start.date().isoformat()
            elif group_by == "month":
                period_key = ticket.created_at.strftime("%Y-%m")
            else:
                period_key = "all"
            
            if period_key not in grouped_data:
                grouped_data[period_key] = {
                    "total": 0,
                    "breached": 0,
                    "on_time": 0
                }
            
            grouped_data[period_key]["total"] += 1
            
            assessment = await self.assess_sla_risk(ticket)
            if assessment.get("time_remaining_hours") is not None:
                if assessment["time_remaining_hours"] <= 0:
                    grouped_data[period_key]["breached"] += 1
                else:
                    grouped_data[period_key]["on_time"] += 1
        
        # Calculate trends
        periods = sorted(grouped_data.keys())
        breach_trend = []
        for period in periods:
            data = grouped_data[period]
            breach_rate = (data["breached"] / data["total"] * 100) if data["total"] > 0 else 0
            breach_trend.append({
                "period": period,
                "breach_rate": breach_rate,
                "total": data["total"]
            })
        
        return {
            "summary": metrics,
            "grouped_by": group_by,
            "breach_trend": breach_trend,
            "periods": periods,
            "grouped_data": grouped_data
        }
    
    async def analyze_historical_patterns(
        self,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze historical patterns to predict future SLA breaches
        
        Uses historical data to identify:
        - Peak breach times
        - Common breach causes
        - Agent performance patterns
        - Ticket type patterns
        
        Args:
            days_back: Number of days to analyze
        
        Returns:
            Dict with pattern analysis
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        end_date = datetime.now(timezone.utc)
        
        # Get all tickets in period
        stmt = select(Ticket).where(
            and_(
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= start_date,
                Ticket.created_at <= end_date
            )
        )
        tickets = self.db.execute(stmt).scalars().all()
        
        # Analyze patterns
        patterns = {
            "peak_breach_hours": self._analyze_peak_breach_hours(tickets),
            "common_breach_causes": self._analyze_breach_causes(tickets),
            "agent_performance": self._analyze_agent_performance(tickets),
            "ticket_type_patterns": self._analyze_ticket_type_patterns(tickets),
            "priority_patterns": self._analyze_priority_patterns(tickets),
            "resolution_time_distribution": self._analyze_resolution_times(tickets)
        }
        
        return {
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "total_tickets_analyzed": len(tickets),
            "patterns": patterns,
            "insights": self._generate_insights(patterns)
        }
    
    def _analyze_peak_breach_hours(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze which hours of day have most breaches"""
        hour_breaches = {}
        hour_totals = {}
        
        for ticket in tickets:
            hour = ticket.created_at.hour
            hour_totals[hour] = hour_totals.get(hour, 0) + 1
            
            # Check if breached (simplified - would need actual resolution times)
            # For now, use status as proxy
            if ticket.status == TicketStatus.RESOLVED:
                # Calculate if it was likely breached
                # This is simplified - real implementation would check SLA
                pass
        
        return {
            "hourly_distribution": hour_totals,
            "peak_hours": sorted(hour_totals.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def _analyze_breach_causes(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze common causes of SLA breaches"""
        causes = {
            "unassigned": 0,
            "high_priority": 0,
            "complex_issues": 0,
            "waiting_customer": 0,
            "other": 0
        }
        
        for ticket in tickets:
            # Simplified analysis - would need more data
            if not ticket.assigned_to_id:
                causes["unassigned"] += 1
            elif ticket.priority in [TicketPriority.HIGH, TicketPriority.URGENT]:
                causes["high_priority"] += 1
        
        return causes
    
    def _analyze_agent_performance(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze agent performance patterns"""
        agent_stats = {}
        
        for ticket in tickets:
            if ticket.assigned_to_id:
                agent_id = ticket.assigned_to_id
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {
                        "total": 0,
                        "on_time": 0,
                        "breached": 0
                    }
                
                agent_stats[agent_id]["total"] += 1
                # Simplified - would need actual SLA check
                agent_stats[agent_id]["on_time"] += 1
        
        return agent_stats
    
    def _analyze_ticket_type_patterns(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze patterns by ticket type"""
        type_stats = {}
        
        for ticket in tickets:
            ticket_type = ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else str(ticket.ticket_type)
            if ticket_type not in type_stats:
                type_stats[ticket_type] = {
                    "total": 0,
                    "avg_resolution_hours": 0,
                    "breach_rate": 0
                }
            
            type_stats[ticket_type]["total"] += 1
        
        return type_stats
    
    def _analyze_priority_patterns(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze patterns by priority"""
        priority_stats = {}
        
        for ticket in tickets:
            priority = ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority)
            if priority not in priority_stats:
                priority_stats[priority] = {
                    "total": 0,
                    "breach_rate": 0
                }
            
            priority_stats[priority]["total"] += 1
        
        return priority_stats
    
    def _analyze_resolution_times(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Analyze resolution time distribution"""
        resolution_times = []
        
        for ticket in tickets:
            if ticket.status == TicketStatus.RESOLVED and ticket.resolved_at:
                hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                resolution_times.append(hours)
        
        if not resolution_times:
            return {"average": 0, "median": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(resolution_times)
        return {
            "average": sum(resolution_times) / len(resolution_times),
            "median": sorted_times[len(sorted_times) // 2],
            "p95": sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0],
            "p99": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0],
            "min": min(resolution_times),
            "max": max(resolution_times)
        }
    
    def _generate_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from patterns"""
        insights = []
        
        # Analyze peak hours
        peak_hours = patterns.get("peak_breach_hours", {}).get("peak_hours", [])
        if peak_hours:
            insights.append(f"Peak ticket creation hours: {', '.join([f'{h[0]}:00' for h in peak_hours[:3]])}")
        
        # Analyze causes
        causes = patterns.get("common_breach_causes", {})
        if causes.get("unassigned", 0) > 10:
            insights.append(f"⚠️ {causes['unassigned']} tickets were unassigned - consider auto-assignment")
        
        # Analyze resolution times
        resolution = patterns.get("resolution_time_distribution", {})
        if resolution.get("average", 0) > 24:
            insights.append(f"⚠️ Average resolution time is {resolution['average']:.1f} hours - consider process improvements")
        
        return insights
    
    async def predict_breach_with_ml(
        self,
        ticket: Ticket,
        use_historical: bool = True
    ) -> Dict[str, Any]:
        """
        Predict SLA breach using ML-based approach with historical data
        
        Args:
            ticket: Ticket to predict
            use_historical: Use historical patterns in prediction
        
        Returns:
            Dict with ML-based prediction
        """
        # Base prediction from current assessment
        base_assessment = await self.assess_sla_risk(ticket)
        
        # Get historical patterns if enabled
        historical_factors = {}
        if use_historical:
            patterns = await self.analyze_historical_patterns(days_back=30)
            historical_factors = {
                "hour_of_day_factor": self._get_hour_factor(ticket.created_at.hour, patterns),
                "ticket_type_factor": self._get_type_factor(ticket, patterns),
                "priority_factor": self._get_priority_factor(ticket, patterns),
                "agent_factor": self._get_agent_factor(ticket, patterns) if ticket.assigned_to_id else 1.2
            }
        
        # Calculate ML-adjusted probability
        base_probability = base_assessment.get("breach_probability", 0.0)
        
        # Apply historical factors
        ml_adjusted_probability = base_probability
        if historical_factors:
            # Weighted average of factors
            factor_sum = sum(historical_factors.values())
            factor_avg = factor_sum / len(historical_factors) if historical_factors else 1.0
            ml_adjusted_probability = min(1.0, base_probability * factor_avg)
        
        # Determine confidence based on data quality
        confidence = 0.7  # Base confidence
        if use_historical and historical_factors:
            confidence = 0.85  # Higher confidence with historical data
        
        return {
            "base_prediction": base_assessment,
            "ml_adjusted_probability": ml_adjusted_probability,
            "confidence": confidence,
            "historical_factors": historical_factors,
            "predicted_breach_time": (predicted_time := await self._predict_breach_time(ticket, ml_adjusted_probability)) and predicted_time.isoformat() or None,
            "recommendations": self._generate_ml_recommendations(ml_adjusted_probability, historical_factors)
        }
    
    def _get_hour_factor(self, hour: int, patterns: Dict[str, Any]) -> float:
        """Get risk factor based on hour of day"""
        peak_hours = patterns.get("patterns", {}).get("peak_breach_hours", {}).get("peak_hours", [])
        peak_hour_values = [h[0] for h in peak_hours]
        
        if hour in peak_hour_values:
            return 1.3  # Higher risk during peak hours
        return 1.0
    
    def _get_type_factor(self, ticket: Ticket, patterns: Dict[str, Any]) -> float:
        """Get risk factor based on ticket type"""
        type_patterns = patterns.get("patterns", {}).get("ticket_type_patterns", {})
        ticket_type = ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else str(ticket.ticket_type)
        
        type_stats = type_patterns.get(ticket_type, {})
        breach_rate = type_stats.get("breach_rate", 0)
        
        if breach_rate > 0.3:
            return 1.2  # Higher risk for types with high breach rate
        return 1.0
    
    def _get_priority_factor(self, ticket: Ticket, patterns: Dict[str, Any]) -> float:
        """Get risk factor based on priority"""
        priority_patterns = patterns.get("patterns", {}).get("priority_patterns", {})
        priority = ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority)
        
        priority_stats = priority_patterns.get(priority, {})
        breach_rate = priority_stats.get("breach_rate", 0)
        
        if breach_rate > 0.2:
            return 1.15
        return 1.0
    
    def _get_agent_factor(self, ticket: Ticket, patterns: Dict[str, Any]) -> float:
        """Get risk factor based on assigned agent performance"""
        agent_patterns = patterns.get("patterns", {}).get("agent_performance", {})
        agent_stats = agent_patterns.get(ticket.assigned_to_id, {})
        
        if agent_stats:
            total = agent_stats.get("total", 0)
            on_time = agent_stats.get("on_time", 0)
            if total > 0:
                on_time_rate = on_time / total
                if on_time_rate < 0.7:
                    return 1.25  # Higher risk with low-performing agent
                elif on_time_rate > 0.9:
                    return 0.9  # Lower risk with high-performing agent
        
        return 1.0
    
    async def _predict_breach_time(self, ticket: Ticket, probability: float) -> Optional[datetime]:
        """Predict when breach will occur"""
        if probability < 0.5:
            return None
        
        # Estimate based on probability and current time remaining
        assessment = await self.assess_sla_risk(ticket)
        time_remaining = assessment.get("time_remaining_hours", 0)
        
        if time_remaining > 0:
            # Adjust based on probability
            estimated_hours = time_remaining * (1 - probability)
            return datetime.now(timezone.utc) + timedelta(hours=estimated_hours)
        
        return datetime.now(timezone.utc)
    
    def _generate_ml_recommendations(
        self,
        probability: float,
        factors: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on ML prediction"""
        recommendations = []
        
        if probability > 0.7:
            recommendations.append("🚨 HIGH RISK: Immediate action required")
            recommendations.append("Consider escalating to senior agent")
            recommendations.append("Notify manager and customer proactively")
        
        if factors.get("agent_factor", 1.0) > 1.2:
            recommendations.append("⚠️ Assigned agent has below-average performance - consider reassignment")
        
        if factors.get("hour_of_day_factor", 1.0) > 1.2:
            recommendations.append("⚠️ Peak hours detected - ensure adequate coverage")
        
        return recommendations


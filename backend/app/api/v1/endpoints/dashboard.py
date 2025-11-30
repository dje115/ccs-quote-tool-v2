#!/usr/bin/env python3
"""
Dashboard endpoints for CRM analytics and AI-powered insights
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, extract
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import calendar
import asyncio

from app.core.database import get_db, get_async_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.tenant import User, Tenant
from app.models.crm import Customer, CustomerStatus, Contact
from app.models.leads import Lead, LeadStatus
from app.models.quotes import Quote, QuoteStatus
from app.models.opportunities import Opportunity, OpportunityStage
from app.models.helpdesk import Ticket
from app.models.sla_compliance import SLAComplianceRecord, SLABreachAlert
from app.services.ai_analysis_service import AIAnalysisService
from app.core.api_keys import get_api_keys

router = APIRouter()


class DashboardStats(BaseModel):
    total_discovery: int
    total_leads: int
    total_prospects: int
    total_opportunities: int
    total_customers: int
    total_cold_leads: int
    total_inactive: int
    total_quotes: int
    quotes_pending: int
    quotes_accepted: int
    total_revenue: float
    avg_deal_value: float
    conversion_rate: float
    # Opportunity metrics
    active_opportunities: int
    opportunities_qualified: int
    opportunities_proposal_sent: int
    opportunities_closed_won: int
    opportunities_total_value: float
    # Lifecycle distribution
    lifecycle_distribution: Dict[str, int]
    # SLA metrics
    sla_compliance_rate: float
    sla_active_breaches: int
    sla_tickets_at_risk: int
    sla_total_tickets: int


class ConversionFunnelItem(BaseModel):
    status: str
    count: int
    percentage: float
    color: str


class RecentActivity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: str
    icon: str


class MonthlyTrend(BaseModel):
    month: str
    new_leads: int
    converted: int
    revenue: float


class AIInsight(BaseModel):
    type: str
    title: str
    description: str
    priority: str
    action: str | None


class PipelineStageItem(BaseModel):
    stage: str
    count: int
    total_value: float
    percentage: float


class DashboardResponse(BaseModel):
    stats: DashboardStats
    conversion_funnel: List[ConversionFunnelItem]
    pipeline_stages: List[PipelineStageItem]  # Opportunity pipeline stages
    recent_activity: List[RecentActivity]
    monthly_trends: List[MonthlyTrend]
    ai_insights: List[AIInsight]
    top_leads: List[Dict[str, Any]]


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get comprehensive dashboard data
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    All database queries are executed asynchronously, allowing Uvicorn
    to serve other clients concurrently.
    """
    
    try:
        tenant_id = current_tenant.id
        
        # Get discovery/leads count from Lead table (discoveries)
        discovery_result = await db.execute(
            select(func.count(Lead.id)).where(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.is_deleted == False
                )
            )
        )
        discovery_count = discovery_result.scalar() or 0
        
        print(f"🔍 Dashboard Debug - Tenant ID: {tenant_id}")
        print(f"🔍 Dashboard Debug - Discovery Count: {discovery_count}")
        
        # Get customer counts by status
        # Note: "total_leads" in frontend refers to discoveries from Lead table, not Customer.LEAD status
        # Execute all count queries in parallel for better performance
        leads_result, prospects_result, opportunities_result, customers_result, cold_leads_result, inactive_result, quotes_result = await asyncio.gather(
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status == CustomerStatus.LEAD,
                    Customer.is_deleted == False
                )
            )),
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status == CustomerStatus.PROSPECT,
                    Customer.is_deleted == False
                )
            )),
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status == CustomerStatus.OPPORTUNITY,
                    Customer.is_deleted == False
                )
            )),
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status == CustomerStatus.CUSTOMER,
                    Customer.is_deleted == False
                )
            )),
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status == CustomerStatus.COLD_LEAD,
                    Customer.is_deleted == False
                )
            )),
            db.execute(select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.is_deleted == False,
                    or_(
                        Customer.status == CustomerStatus.INACTIVE,
                        Customer.status == CustomerStatus.LOST
                    )
                )
            )),
            db.execute(select(func.count(Quote.id)).where(
                and_(
                    Quote.tenant_id == tenant_id,
                    Quote.is_deleted == False
                )
            ))
        )
        
        leads_count = leads_result.scalar() or 0
        prospects_count = prospects_result.scalar() or 0
        opportunities_count = opportunities_result.scalar() or 0
        customers_count = customers_result.scalar() or 0
        cold_leads_count = cold_leads_result.scalar() or 0
        inactive_count = inactive_result.scalar() or 0
        total_quotes = quotes_result.scalar() or 0
        
        # Get opportunity metrics
        opportunity_queries = await asyncio.gather(
            db.execute(select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.is_deleted == False,
                    ~Opportunity.stage.in_([OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST])
                )
            )),
            db.execute(select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.QUALIFIED,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.PROPOSAL_SENT,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.CLOSED_WON,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.is_deleted == False,
                    Opportunity.estimated_value.isnot(None)
                )
            ))
        )
        
        active_opportunities = opportunity_queries[0].scalar() or 0
        opportunities_qualified = opportunity_queries[1].scalar() or 0
        opportunities_proposal_sent = opportunity_queries[2].scalar() or 0
        opportunities_closed_won = opportunity_queries[3].scalar() or 0
        opp_value = opportunity_queries[4].scalar()
        opportunities_total_value = float(opp_value) if opp_value else 0.0
        
        # Get lifecycle distribution (using existing statuses - INACTIVE for dormant, LOST for closed lost)
        lifecycle_distribution = {
            "LEAD": leads_count,
            "PROSPECT": prospects_count,
            "CUSTOMER": customers_count,
            "INACTIVE": inactive_count,  # Maps to DORMANT in lifecycle service
            "LOST": 0  # Will be calculated separately if needed
        }
        
        # Get LOST status count
        lost_result = await db.execute(select(func.count(Customer.id)).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.status == CustomerStatus.LOST,
                Customer.is_deleted == False
            )
        ))
        lifecycle_distribution["LOST"] = lost_result.scalar() or 0
        
        # Execute remaining quote queries in parallel
        quotes_pending_result, quotes_accepted_result, revenue_result = await asyncio.gather(
            db.execute(select(func.count(Quote.id)).where(
                and_(
                    Quote.tenant_id == tenant_id,
                    Quote.is_deleted == False,
                    or_(
                        Quote.status == QuoteStatus.DRAFT,
                        Quote.status == QuoteStatus.SENT
                    )
                )
            )),
            db.execute(select(func.count(Quote.id)).where(
                and_(
                    Quote.tenant_id == tenant_id,
                    Quote.status == QuoteStatus.ACCEPTED,
                    Quote.is_deleted == False
                )
            )),
            db.execute(select(func.sum(Quote.total_amount)).where(
                and_(
                    Quote.tenant_id == tenant_id,
                    Quote.status == QuoteStatus.ACCEPTED,
                    Quote.is_deleted == False
                )
            ))
        )
        
        quotes_pending = quotes_pending_result.scalar() or 0
        quotes_accepted = quotes_accepted_result.scalar() or 0
        revenue_value = revenue_result.scalar()
        total_revenue = float(revenue_value) if revenue_value else 0.0
        
        avg_deal_value = (total_revenue / quotes_accepted) if quotes_accepted > 0 else 0.0
        
        # Conversion rate (leads to customers)
        total_pipeline = leads_count + prospects_count + customers_count
        conversion_rate = (customers_count / total_pipeline * 100) if total_pipeline > 0 else 0.0
        
        # Conversion funnel
        funnel_total = leads_count + prospects_count + customers_count + cold_leads_count
        conversion_funnel = [
            ConversionFunnelItem(
                status="Leads",
                count=leads_count,
                percentage=(leads_count / funnel_total * 100) if funnel_total > 0 else 0,
                color="#3498db"
            ),
            ConversionFunnelItem(
                status="Prospects",
                count=prospects_count,
                percentage=(prospects_count / funnel_total * 100) if funnel_total > 0 else 0,
                color="#9b59b6"
            ),
            ConversionFunnelItem(
                status="Customers",
                count=customers_count,
                percentage=(customers_count / funnel_total * 100) if funnel_total > 0 else 0,
                color="#2ecc71"
            ),
            ConversionFunnelItem(
                status="Cold/Inactive",
                count=cold_leads_count + inactive_count,
                percentage=((cold_leads_count + inactive_count) / funnel_total * 100) if funnel_total > 0 else 0,
                color="#95a5a6"
            )
        ]
        
        # Opportunity pipeline stages
        pipeline_stage_queries = await asyncio.gather(
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.QUALIFIED,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.SCOPING,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.PROPOSAL_SENT,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.NEGOTIATION,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.VERBAL_YES,
                    Opportunity.is_deleted == False
                )
            )),
            db.execute(select(func.count(Opportunity.id), func.sum(Opportunity.estimated_value)).where(
                and_(
                    Opportunity.tenant_id == tenant_id,
                    Opportunity.stage == OpportunityStage.CLOSED_WON,
                    Opportunity.is_deleted == False
                )
            ))
        )
        
        pipeline_stages = []
        stage_labels = ["Qualified", "Scoping", "Proposal Sent", "Negotiation", "Verbal Yes", "Closed Won"]
        total_pipeline_value = 0.0
        
        for idx, result in enumerate(pipeline_stage_queries):
            row = result.first()
            count = row[0] if row else 0
            value = float(row[1]) if row and row[1] else 0.0
            total_pipeline_value += value
            
            pipeline_stages.append(PipelineStageItem(
                stage=stage_labels[idx],
                count=count,
                total_value=value,
                percentage=0.0  # Will calculate after we have total
            ))
        
        # Calculate percentages
        for stage in pipeline_stages:
            stage.percentage = (stage.total_value / total_pipeline_value * 100) if total_pipeline_value > 0 else 0.0
        
        # Recent activity (last 10 items)
        recent_customers_result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.is_deleted == False
                )
            ).order_by(Customer.created_at.desc()).limit(5)
        )
        recent_customers = recent_customers_result.scalars().all()
        
        recent_activity = []
        for customer in recent_customers:
            recent_activity.append(RecentActivity(
                id=str(customer.id),
                type="customer",
                title=f"New {customer.status.value}",
                description=customer.company_name,
                timestamp=customer.created_at.isoformat(),
                icon="user-plus"
            ))
        
        # Monthly trends (last 6 months)
        # Execute all monthly queries in parallel for better performance
        monthly_trends = []
        now = datetime.utcnow()
        month_queries = []
        month_starts = []
        
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            month_starts.append(month_start)
            
            # Prepare queries for parallel execution (create coroutines)
            month_queries.append([
                db.execute(select(func.count(Lead.id)).where(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= month_start,
                        Lead.created_at <= month_end,
                        Lead.is_deleted == False
                    )
                )),
                db.execute(select(func.count(Customer.id)).where(
                    and_(
                        Customer.tenant_id == tenant_id,
                        Customer.status == CustomerStatus.CUSTOMER,
                        Customer.is_deleted == False,
                        Customer.created_at >= month_start,
                        Customer.created_at <= month_end
                    )
                )),
                db.execute(select(func.sum(Quote.total_amount)).where(
                    and_(
                        Quote.tenant_id == tenant_id,
                        Quote.status == QuoteStatus.ACCEPTED,
                        Quote.is_deleted == False,
                        Quote.created_at >= month_start,
                        Quote.created_at <= month_end
                    )
                ))
            ])
        
        # Execute all monthly queries in parallel (flatten nested structure)
        all_month_results = await asyncio.gather(*[asyncio.gather(*queries) for queries in month_queries])
        
        # Process results
        for idx, (new_leads_result, converted_result, month_revenue_result) in enumerate(all_month_results):
            new_leads = new_leads_result.scalar() or 0
            converted = converted_result.scalar() or 0
            revenue_value = month_revenue_result.scalar()
            month_revenue = float(revenue_value) if revenue_value else 0.0
            
            monthly_trends.append(MonthlyTrend(
                month=calendar.month_abbr[month_starts[idx].month],
                new_leads=new_leads,
                converted=converted,
                revenue=month_revenue
            ))
        
        # AI-powered insights
        ai_insights = []
        
        # Insight 1: High-value leads
        high_score_leads_result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status.in_([CustomerStatus.LEAD, CustomerStatus.PROSPECT, CustomerStatus.OPPORTUNITY]),
                    Customer.lead_score >= 70,
                    Customer.is_deleted == False
                )
            ).limit(5)
        )
        high_score_leads = high_score_leads_result.scalars().all()
        
        if high_score_leads:
            ai_insights.append(AIInsight(
                type="opportunity",
                title=f"{len(high_score_leads)} High-Value Leads Require Attention",
                description=f"You have {len(high_score_leads)} leads with scores above 70. These are prime conversion opportunities.",
                priority="high",
                action="view_leads"
            ))
        
        # Insight 2: Cold leads needing follow-up
        if cold_leads_count > 0:
            ai_insights.append(AIInsight(
                type="warning",
                title=f"{cold_leads_count} Cold Leads Need Re-engagement",
                description="Consider running a re-engagement campaign to revive these opportunities.",
                priority="medium",
                action="view_cold_leads"
            ))
        
        # Insight 3: Conversion rate analysis
        if conversion_rate < 20 and leads_count > 5:
            ai_insights.append(AIInsight(
                type="alert",
                title="Low Conversion Rate Detected",
                description=f"Your lead-to-customer conversion rate is {conversion_rate:.1f}%. Consider improving lead qualification.",
                priority="high",
                action="analyze_conversion"
            ))
        elif conversion_rate > 30:
            ai_insights.append(AIInsight(
                type="success",
                title="Excellent Conversion Performance",
                description=f"Your {conversion_rate:.1f}% conversion rate is excellent! Keep up the good work.",
                priority="low",
                action=None
            ))
        
        # Insight 4: Pending quotes
        if quotes_pending > 5:
            ai_insights.append(AIInsight(
                type="info",
                title=f"{quotes_pending} Quotes Awaiting Response",
                description="Follow up on pending quotes to accelerate deal closure.",
                priority="medium",
                action="view_quotes"
            ))
        
        # Top leads by score
        top_leads_result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.is_deleted == False,
                    Customer.status.in_([CustomerStatus.LEAD, CustomerStatus.PROSPECT, CustomerStatus.OPPORTUNITY])
                )
            ).order_by(Customer.lead_score.desc()).limit(10)
        )
        top_leads_query = top_leads_result.scalars().all()
        
        top_leads = [
            {
                "id": str(lead.id),
                "company_name": lead.company_name,
                "status": lead.status.value,
                "lead_score": lead.lead_score or 0,
                "created_at": lead.created_at.isoformat() if lead.created_at else None
            }
            for lead in top_leads_query
        ]
        
        # SLA Metrics
        # Get total tickets with SLA policies
        total_tickets_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.tenant_id == tenant_id,
                    Ticket.sla_policy_id.isnot(None),
                    Ticket.status.notin_(['closed', 'resolved'])
                )
            )
        )
        sla_total_tickets = total_tickets_result.scalar() or 0
        
        # Get active breach alerts (unacknowledged)
        active_breaches_result = await db.execute(
            select(func.count(SLABreachAlert.id)).where(
                and_(
                    SLABreachAlert.tenant_id == tenant_id,
                    SLABreachAlert.acknowledged == False
                )
            )
        )
        sla_active_breaches = active_breaches_result.scalar() or 0
        
        # Get tickets at risk (80%+ of SLA time used)
        # This is a simplified calculation - in production, you'd calculate based on actual SLA targets
        tickets_at_risk_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.tenant_id == tenant_id,
                    Ticket.sla_policy_id.isnot(None),
                    Ticket.status.notin_(['closed', 'resolved'])
                )
            )
        )
        sla_tickets_at_risk = tickets_at_risk_result.scalar() or 0  # Simplified - would need actual calculation
        
        # Calculate compliance rate from compliance records
        compliance_records_result = await db.execute(
            select(SLAComplianceRecord).where(
                and_(
                    SLAComplianceRecord.tenant_id == tenant_id,
                    SLAComplianceRecord.created_at >= datetime.now() - timedelta(days=30)
                )
            )
        )
        compliance_records = compliance_records_result.scalars().all()
        
        sla_compliance_rate = 0.0
        if compliance_records:
            compliant_count = sum(1 for r in compliance_records if r.compliant)
            sla_compliance_rate = round((compliant_count / len(compliance_records)) * 100, 1)
        
        print(f"🔍 Dashboard Debug - Returning stats: total_leads={discovery_count}, total_discovery={discovery_count}")
        
        return DashboardResponse(
            stats=DashboardStats(
                total_discovery=discovery_count,
                total_leads=leads_count,  # Show customers with LEAD status (not discoveries)
                total_prospects=prospects_count,
                total_opportunities=opportunities_count,
                total_customers=customers_count,
                total_cold_leads=cold_leads_count,
                total_inactive=inactive_count,
                total_quotes=total_quotes,
                quotes_pending=quotes_pending,
                quotes_accepted=quotes_accepted,
                total_revenue=total_revenue,
                avg_deal_value=avg_deal_value,
                conversion_rate=round(conversion_rate, 1),
                active_opportunities=active_opportunities,
                opportunities_qualified=opportunities_qualified,
                opportunities_proposal_sent=opportunities_proposal_sent,
                opportunities_closed_won=opportunities_closed_won,
                opportunities_total_value=opportunities_total_value,
                lifecycle_distribution=lifecycle_distribution,
                sla_compliance_rate=sla_compliance_rate,
                sla_active_breaches=sla_active_breaches,
                sla_tickets_at_risk=sla_tickets_at_risk,
                sla_total_tickets=sla_total_tickets
            ),
            conversion_funnel=conversion_funnel,
            pipeline_stages=pipeline_stages,
            recent_activity=recent_activity,
            monthly_trends=monthly_trends,
            ai_insights=ai_insights,
            top_leads=top_leads
        )
        
    except Exception as e:
        print(f"[ERROR] Dashboard error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class AIQueryRequest(BaseModel):
    query: str


class AIQueryResponse(BaseModel):
    """
    AI Query Response with visualization support
    
    visualization_type options:
    - "bar_chart": For comparing categories (e.g., customers by status)
    - "line_chart": For trends over time (e.g., monthly growth)
    - "pie_chart": For distribution/percentage breakdown
    - "doughnut_chart": Alternative to pie chart with center space
    - "area_chart": For cumulative trends
    - None: Text-only response
    
    chart_data format depends on visualization_type:
    - bar/pie/doughnut: {"labels": [...], "values": [...], "colors": [...]}
    - line/area: {"labels": [...], "datasets": [{"label": "...", "data": [...], "color": "..."}]}
    """
    answer: str
    data: Dict[str, Any] | None
    visualization_type: str | None
    chart_data: Dict[str, Any] | None = None
    suggested_followup: List[str] | None = None


@router.post("/ai-query", response_model=AIQueryResponse)
async def ai_dashboard_query(
    request: AIQueryRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    AI-powered dashboard query system
    
    IMPORTANT: This endpoint provides comprehensive CRM context to the AI assistant.
    As we add more modules (quotes, campaigns, tasks, etc.), expand the context below
    to include relevant data from those modules.
    
    Current modules included:
    - Customers (all statuses)
    - Contacts
    - Monthly trends (last 6 months)
    - Top performing leads
    
    Future modules to add:
    - Quotes (pending, accepted, rejected)
    - Lead generation campaigns
    - Tasks and reminders
    - Customer interactions history
    - Financial analysis data
    """
    
    try:
        tenant_id = current_tenant.id
        
        # ===== API KEY RESOLUTION: Tenant keys first, then fall back to system keys =====
        # Get API keys using the centralized helper function
        # This checks tenant keys first, then falls back to system-wide keys from admin portal
        # Use sync session for get_api_keys (it expects sync session)
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            api_keys = get_api_keys(sync_db, current_tenant)
        finally:
            sync_db.close()
        
        # Initialize AI service with resolved API keys and tenant context
        # Use sync session for AI service (it may need sync operations)
        sync_db_for_ai = SessionLocal()
        try:
            ai_service = AIAnalysisService(
                openai_api_key=api_keys.openai,
                companies_house_api_key=api_keys.companies_house,
                google_maps_api_key=api_keys.google_maps,
                tenant_id=current_tenant.id,
                db=sync_db_for_ai
            )
        finally:
            sync_db_for_ai.close()
        
        # ===== CUSTOMER DATA =====
        total_customers_result = await db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.is_deleted == False
                )
            )
        )
        total_customers = total_customers_result.scalar() or 0
        
        customers_by_status = {}
        for status in CustomerStatus:
            count_result = await db.execute(
                select(func.count(Customer.id)).where(
                    and_(
                        Customer.tenant_id == tenant_id,
                        Customer.status == status,
                        Customer.is_deleted == False
                    )
                )
            )
            customers_by_status[status.value] = count_result.scalar() or 0
        
        # ===== CONTACT DATA =====
        from app.models.crm import Contact
        total_contacts_result = await db.execute(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.tenant_id == tenant_id,
                    Contact.is_deleted == False
                )
            )
        )
        total_contacts = total_contacts_result.scalar() or 0
        
        # ===== MONTHLY TRENDS (Last 6 months) =====
        now = datetime.utcnow()
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            # Count new discoveries (leads) from Lead table for AI query context
            new_leads_result = await db.execute(
                select(func.count(Lead.id)).where(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= month_start,
                        Lead.created_at <= month_end,
                        Lead.is_deleted == False
                    )
                )
            )
            new_leads = new_leads_result.scalar() or 0
            
            new_customers_result = await db.execute(
                select(func.count(Customer.id)).where(
                    and_(
                        Customer.tenant_id == tenant_id,
                        Customer.created_at >= month_start,
                        Customer.created_at <= month_end,
                        Customer.status == CustomerStatus.CUSTOMER,
                        Customer.is_deleted == False
                    )
                )
            )
            new_customers = new_customers_result.scalar() or 0
            
            monthly_data.append({
                "month": month_date.strftime("%B %Y"),
                "new_leads": new_leads,
                "new_customers": new_customers
            })
        
        # ===== TOP PERFORMING LEADS =====
        top_leads_result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_id,
                    Customer.status.in_([CustomerStatus.LEAD, CustomerStatus.PROSPECT]),
                    Customer.is_deleted == False
                )
            ).order_by(Customer.lead_score.desc()).limit(5)
        )
        top_leads = top_leads_result.scalars().all()
        
        top_leads_info = [
            f"{lead.company_name} (Score: {lead.lead_score or 0})"
            for lead in top_leads
        ]
        
        # ===== PREPARE USER PROFILE CONTEXT =====
        # Extract user information for personalization
        user_profile = {
            "first_name": current_user.first_name or "",
            "last_name": current_user.last_name or "",
            "email": current_user.email or "",
            "full_name": f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email or "User"
        }
        
        # Build user context string
        user_context_parts = []
        if user_profile["full_name"] and user_profile["full_name"] != "User":
            user_context_parts.append(f"User Name: {user_profile['full_name']}")
        if user_profile["email"]:
            user_context_parts.append(f"User Email: {user_profile['email']}")
        
        user_context_str = "\n".join(user_context_parts) if user_context_parts else ""
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"User context being passed to AI: {user_context_str}")
        logger.debug(f"User profile: {user_profile}")
        
        # ===== PREPARE TENANT BUSINESS PROFILE CONTEXT =====
        # Extract tenant business information for AI context
        tenant_profile = {
            "company_name": current_tenant.company_name or current_tenant.name,
            "company_description": current_tenant.company_description or "",
            "products_services": current_tenant.products_services or [],
            "unique_selling_points": current_tenant.unique_selling_points or [],
            "target_markets": current_tenant.target_markets or []
        }
        
        # Build tenant context string - format matches prompt expectations
        tenant_context_parts = []
        
        # Always include company name
        tenant_context_parts.append(f"Company: {tenant_profile['company_name']}")
        
        if tenant_profile["company_description"]:
            tenant_context_parts.append(f"About: {tenant_profile['company_description']}")
        
        if tenant_profile["products_services"]:
            services_list = ", ".join(tenant_profile["products_services"][:15])  # Increased limit
            tenant_context_parts.append(f"Products/Services: {services_list}")
        
        if tenant_profile["unique_selling_points"]:
            usps_list = ", ".join(tenant_profile["unique_selling_points"][:10])  # Increased limit
            tenant_context_parts.append(f"Unique Selling Points: {usps_list}")
        
        if tenant_profile["target_markets"]:
            markets_list = ", ".join(tenant_profile["target_markets"][:10])
            tenant_context_parts.append(f"Target Markets: {markets_list}")
        
        tenant_context_str = "\n".join(tenant_context_parts) if tenant_context_parts else f"Company: {tenant_profile['company_name']}\nNo additional company profile information available."
        
        # ===== PREPARE COMPREHENSIVE CONTEXT FOR AI =====
        # Build CRM data snapshot (without the query - query is passed separately)
        context = f"""
CUSTOMERS & LEADS:
- Total Customers/Leads in System: {total_customers}
- Active Leads: {customers_by_status.get('LEAD', 0)}
- Qualified Prospects: {customers_by_status.get('PROSPECT', 0)}
- Active Customers: {customers_by_status.get('CUSTOMER', 0)}
- Cold Leads: {customers_by_status.get('COLD_LEAD', 0)}
- Inactive Customers: {customers_by_status.get('INACTIVE', 0)}
- Lost Opportunities: {customers_by_status.get('LOST', 0)}

CONTACTS:
- Total Contacts: {total_contacts}
- Average Contacts per Customer: {round(total_contacts / total_customers, 1) if total_customers > 0 else 0}

MONTHLY TRENDS (Last 6 Months):
{chr(10).join([f"- {m['month']}: {m['new_leads']} new leads, {m['new_customers']} converted to customers" for m in monthly_data])}

TOP PERFORMING LEADS:
{chr(10).join([f"- {lead}" for lead in top_leads_info]) if top_leads_info else "- No leads with scores yet"}
"""
        
        # Get AI response using database prompt with tenant context and user context
        answer = await ai_service.get_dashboard_insight(
            context, 
            query=request.query, 
            tenant_context=tenant_context_str,
            user_context=user_context_str
        )
        
        # ===== DETERMINE VISUALIZATION TYPE AND GENERATE CHART DATA =====
        query_lower = request.query.lower()
        viz_type = None
        viz_data = None
        chart_data = None
        
        # Define color palette for charts
        status_colors = {
            "LEAD": "#667eea",
            "PROSPECT": "#f093fb",
            "CUSTOMER": "#4facfe",
            "COLD_LEAD": "#fa709a",
            "INACTIVE": "#95a5a6",
            "LOST": "#e74c3c"
        }
        
        # Detect visualization needs from query
        if any(word in query_lower for word in ["how many", "count", "number of", "total", "breakdown by status"]):
            viz_type = "bar_chart"
            viz_data = customers_by_status
            # Generate bar chart data
            labels = []
            values = []
            colors = []
            for status, count in customers_by_status.items():
                if count > 0:  # Only show statuses with data
                    labels.append(status.replace('_', ' ').title())
                    values.append(count)
                    colors.append(status_colors.get(status, "#95a5a6"))
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "label": "Customers by Status",
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 2
                }]
            }
            
        elif any(word in query_lower for word in ["trend", "over time", "monthly", "growth", "last 6 months"]):
            viz_type = "line_chart"
            viz_data = {"monthly_trends": monthly_data}
            # Generate line chart data
            chart_data = {
                "labels": [m["month"] for m in monthly_data],
                "datasets": [
                    {
                        "label": "New Leads",
                        "data": [m["new_leads"] for m in monthly_data],
                        "borderColor": "#667eea",
                        "backgroundColor": "rgba(102, 126, 234, 0.1)",
                        "fill": True,
                        "tension": 0.4
                    },
                    {
                        "label": "New Customers",
                        "data": [m["new_customers"] for m in monthly_data],
                        "borderColor": "#4facfe",
                        "backgroundColor": "rgba(79, 172, 254, 0.1)",
                        "fill": True,
                        "tension": 0.4
                    }
                ]
            }
            
        elif any(word in query_lower for word in ["distribution", "percentage", "pie", "proportion"]):
            viz_type = "doughnut_chart"
            viz_data = customers_by_status
            # Generate doughnut chart data
            labels = []
            values = []
            colors = []
            for status, count in customers_by_status.items():
                if count > 0:  # Only show statuses with data
                    labels.append(status.replace('_', ' ').title())
                    values.append(count)
                    colors.append(status_colors.get(status, "#95a5a6"))
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "label": "Distribution",
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": "#ffffff",
                    "borderWidth": 3
                }]
            }
            
        elif any(word in query_lower for word in ["top", "best", "highest", "leading"]):
            # Show top leads with scores
            viz_type = "bar_chart"
            if top_leads:
                chart_data = {
                    "labels": [lead.company_name for lead in top_leads],
                    "datasets": [{
                        "label": "Lead Score",
                        "data": [lead.lead_score or 0 for lead in top_leads],
                        "backgroundColor": "#f093fb",
                        "borderColor": "#f093fb",
                        "borderWidth": 2
                    }]
                }
        
        # ===== GENERATE SUGGESTED FOLLOW-UP QUESTIONS =====
        suggested_followup = [
            "Show me the trend over the last 6 months",
            "What's the breakdown of customers by status?",
            "Who are my top 5 leads?",
            "How many new customers did we get this month?",
            "What's my conversion rate from leads to customers?"
        ]
        
        return AIQueryResponse(
            answer=answer,
            data=viz_data or customers_by_status,
            visualization_type=viz_type,
            chart_data=chart_data,
            suggested_followup=suggested_followup
        )
        
    except Exception as e:
        print(f"[ERROR] AI query error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/change-status")
async def change_customer_status(
    customer_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Change customer status (lead -> prospect -> customer, etc.)"""
    
    try:
        from sqlalchemy import select
        
        stmt = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == current_tenant.id
            )
        )
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Validate and set new status
        valid_statuses = {
            "lead": CustomerStatus.LEAD,
            "prospect": CustomerStatus.PROSPECT,
            "customer": CustomerStatus.CUSTOMER,
            "cold_lead": CustomerStatus.COLD_LEAD,
            "inactive": CustomerStatus.INACTIVE,
            "lost": CustomerStatus.LOST
        }
        
        if new_status.lower() not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses.keys())}")
        
        old_status = customer.status.value
        customer.status = valid_statuses[new_status.lower()]
        await db.commit()
        
        return {
            "success": True,
            "message": f"Customer status changed from {old_status} to {new_status}",
            "customer_id": customer_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Change status error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


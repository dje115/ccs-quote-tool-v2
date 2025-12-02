#!/usr/bin/env python3
"""
Knowledge Base Service
Manages knowledge base articles and ticket linking
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from datetime import datetime

from app.models.knowledge_base import KnowledgeBaseArticle, KnowledgeBaseTicketLink, ArticleStatus
from app.models.helpdesk import Ticket

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Service for knowledge base management
    
    Features:
    - Article CRUD
    - Search functionality
    - AI-powered suggestions
    - Ticket-to-KB linking
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def create_article(
        self,
        title: str,
        content: str,
        summary: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = ArticleStatus.PUBLISHED.value,
        user_id: Optional[str] = None
    ) -> KnowledgeBaseArticle:
        """Create a new knowledge base article"""
        import uuid
        
        article = KnowledgeBaseArticle(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            title=title,
            content=content,
            summary=summary,
            category=category,
            tags=tags or [],
            status=status,
            created_by=user_id
        )
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        return article
    
    def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[KnowledgeBaseArticle]:
        """Search knowledge base articles"""
        try:
            stmt = select(KnowledgeBaseArticle).where(
                KnowledgeBaseArticle.tenant_id == self.tenant_id,
                KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED.value,
                or_(
                    KnowledgeBaseArticle.title.ilike(f"%{query}%"),
                    KnowledgeBaseArticle.content.ilike(f"%{query}%"),
                    KnowledgeBaseArticle.summary.ilike(f"%{query}%")
                )
            )
            
            if category:
                stmt = stmt.where(KnowledgeBaseArticle.category == category)
            
            stmt = stmt.order_by(KnowledgeBaseArticle.view_count.desc()).limit(limit)
            
            articles = self.db.execute(stmt).scalars().all()
            return articles
        except Exception as e:
            logger.error(f"Error searching articles: {e}", exc_info=True)
            # Rollback any failed transaction
            self.db.rollback()
            # Return empty list on error
            return []
    
    async def suggest_articles_for_ticket(
        self,
        ticket: Ticket,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest knowledge base articles for a ticket
        
        Args:
            ticket: Ticket to find suggestions for
            limit: Maximum number of suggestions
        
        Returns:
            List of suggested articles with relevance scores
        """
        # Extract keywords from ticket
        keywords = self._extract_keywords(ticket.subject + " " + (ticket.description or ""))
        
        # Search for articles
        suggestions = []
        for keyword in keywords[:5]:  # Use top 5 keywords
            articles = self.search_articles(keyword, limit=limit * 2)
            for article in articles:
                # Calculate relevance score
                relevance = self._calculate_relevance(article, ticket, keyword)
                
                suggestions.append({
                    "article": article,
                    "relevance_score": relevance,
                    "matched_keyword": keyword
                })
        
        # Sort by relevance and remove duplicates
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Remove duplicates
        seen_article_ids = set()
        unique_suggestions = []
        for suggestion in suggestions:
            article_id = suggestion["article"].id
            if article_id not in seen_article_ids:
                seen_article_ids.add(article_id)
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= limit:
                    break
        
        return unique_suggestions
    
    def link_article_to_ticket(
        self,
        ticket_id: str,
        article_id: str,
        link_type: str = "linked",
        relevance_score: Optional[int] = None
    ) -> KnowledgeBaseTicketLink:
        """Link a knowledge base article to a ticket"""
        import uuid
        
        link = KnowledgeBaseTicketLink(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            article_id=article_id,
            link_type=link_type,
            relevance_score=relevance_score
        )
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return link
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        import re
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter and count
        keywords = {}
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords[word] = keywords.get(word, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_keywords[:10]]
    
    def _calculate_relevance(
        self,
        article: KnowledgeBaseArticle,
        ticket: Ticket,
        keyword: str
    ) -> int:
        """Calculate relevance score (0-100)"""
        score = 0
        
        # Title match
        if keyword.lower() in article.title.lower():
            score += 40
        
        # Content match
        if keyword.lower() in article.content.lower():
            score += 30
        
        # Category match (if ticket type matches article category)
        if ticket.ticket_type and article.category:
            # Try to match ticket type to article category (flexible matching)
            ticket_type_str = ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else str(ticket.ticket_type)
            if ticket_type_str.lower() in article.category.lower() or article.category.lower() in ticket_type_str.lower():
                score += 20
        
        # View count (popularity)
        if article.view_count > 10:
            score += 10
        
        return min(100, score)
    
    def mark_article_helpful(
        self,
        article_id: str,
        helpful: bool = True
    ):
        """Mark article as helpful or not helpful"""
        article = self.db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == self.tenant_id
        ).first()
        
        if article:
            if helpful:
                article.helpful_count += 1
            else:
                article.not_helpful_count += 1
            
            self.db.commit()
    
    def increment_view_count(self, article_id: str):
        """Increment article view count"""
        article = self.db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == self.tenant_id
        ).first()
        
        if article:
            article.view_count += 1
            self.db.commit()
    
    async def suggest_articles_with_ai(
        self,
        ticket: Ticket,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        AI-powered article suggestions using semantic matching
        
        Uses AI to understand ticket context and find relevant articles
        
        Args:
            ticket: Ticket to find suggestions for
            limit: Maximum number of suggestions
        
        Returns:
            List of suggested articles with AI relevance scores
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        
        try:
            # Get all published articles
            try:
                stmt = select(KnowledgeBaseArticle).where(
                    KnowledgeBaseArticle.tenant_id == self.tenant_id,
                    KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED.value
                )
                all_articles = self.db.execute(stmt).scalars().all()
            except Exception as db_error:
                logger.error(f"Database error in suggest_articles_with_ai: {db_error}", exc_info=True)
                self.db.rollback()
                return []
            
            if not all_articles:
                return []
            
            # Build context for AI
            ticket_type_str = 'N/A'
            if ticket.ticket_type:
                if hasattr(ticket.ticket_type, 'value'):
                    ticket_type_str = ticket.ticket_type.value
                else:
                    ticket_type_str = str(ticket.ticket_type)
            
            priority_str = 'N/A'
            if ticket.priority:
                if hasattr(ticket.priority, 'value'):
                    priority_str = ticket.priority.value
                else:
                    priority_str = str(ticket.priority)
            
            ticket_context = f"""
            Ticket Subject: {ticket.subject or ''}
            Ticket Description: {ticket.description or ticket.original_description or ''}
            Ticket Type: {ticket_type_str}
            Ticket Priority: {priority_str}
            """
            
            # Create article summaries for AI
            article_summaries = []
            for article in all_articles:
                article_summaries.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary or article.content[:200],
                    "category": article.category
                })
            
            # Use AI to find most relevant articles
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            Given the following ticket and knowledge base articles, identify the most relevant articles.
            
            Ticket Context:
            {ticket_context}
            
            Available Articles:
            {chr(10).join([f"- {a['title']}: {a['summary']}" for a in article_summaries[:20]])}
            
            Return a JSON array with article IDs and relevance scores (0-100), ordered by relevance.
            Format: [{{"article_id": "id", "relevance_score": 85, "reason": "explanation"}}]
            """
            
            # Use the new helpdesk_quick_response prompt
            response = await ai_service.generate(
                category=PromptCategory.HELPDESK_QUICK_RESPONSE.value,
                variables={
                    "ticket_subject": ticket.subject or '',
                    "ticket_description": ticket.description or ticket.original_description or '',
                    "ticket_type": ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else str(ticket.ticket_type or 'N/A'),
                    "ticket_priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority or 'N/A')
                },
                max_tokens=500
            )
            
            # Parse AI response
            ai_suggestions = self._parse_ai_suggestions(response, all_articles)
            
            # Fallback to keyword-based if AI fails
            if not ai_suggestions:
                return await self.suggest_articles_for_ticket(ticket, limit)
            
            # Return top suggestions
            return ai_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error in AI-powered suggestions: {e}")
            # Fallback to keyword-based
            return await self.suggest_articles_for_ticket(ticket, limit)
    
    def _parse_ai_suggestions(
        self,
        ai_response: str,
        articles: List[KnowledgeBaseArticle]
    ) -> List[Dict[str, Any]]:
        """Parse AI response into article suggestions"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                suggestions_data = json.loads(json_match.group())
                
                suggestions = []
                article_map = {a.id: a for a in articles}
                
                for item in suggestions_data:
                    article_id = item.get("article_id")
                    if article_id in article_map:
                        suggestions.append({
                            "article": article_map[article_id],
                            "relevance_score": item.get("relevance_score", 50),
                            "reason": item.get("reason", "AI-matched"),
                            "matched_keyword": "AI"
                        })
                
                return sorted(suggestions, key=lambda x: x["relevance_score"], reverse=True)
        except Exception as e:
            logger.error(f"Error parsing AI suggestions: {e}")
        
        return []
    
    async def auto_categorize_article(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Auto-categorize article using AI
        
        Args:
            title: Article title
            content: Article content
        
        Returns:
            Dict with suggested category and tags
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        
        try:
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            Analyze the following knowledge base article and suggest:
            1. A category (e.g., technical, billing, support, feature, troubleshooting)
            2. 3-5 relevant tags
            
            Article Title: {title}
            Article Content: {content[:500]}
            
            Return JSON format:
            {{
                "category": "suggested_category",
                "tags": ["tag1", "tag2", "tag3"],
                "confidence": 0.85
            }}
            """
            
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=200
            )
            
            return self._parse_categorization(response)
            
        except Exception as e:
            logger.error(f"Error in auto-categorization: {e}")
            return {
                "category": None,
                "tags": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _parse_categorization(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI categorization response"""
        import json
        import re
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Error parsing categorization: {e}")
        
        return {
            "category": None,
            "tags": [],
            "confidence": 0.0
        }
    
    async def generate_article_recommendations(
        self,
        article_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate article recommendations based on viewing patterns
        
        Uses collaborative filtering: articles viewed together are recommended
        
        Args:
            article_id: Current article ID
            limit: Number of recommendations
        
        Returns:
            List of recommended articles
        """
        # Get current article
        article = self.db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id,
            KnowledgeBaseArticle.tenant_id == self.tenant_id
        ).first()
        
        if not article:
            return []
        
        # Find articles in same category
        stmt = select(KnowledgeBaseArticle).where(
            KnowledgeBaseArticle.tenant_id == self.tenant_id,
            KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED.value,
            KnowledgeBaseArticle.id != article_id
        )
        
        if article.category:
            stmt = stmt.where(KnowledgeBaseArticle.category == article.category)
        
        # Order by popularity (view count)
        stmt = stmt.order_by(KnowledgeBaseArticle.view_count.desc()).limit(limit * 2)
        
        candidates = self.db.execute(stmt).scalars().all()
        
        # Score candidates based on:
        # - Same category (high weight)
        # - Shared tags (medium weight)
        # - Popularity (low weight)
        recommendations = []
        for candidate in candidates:
            score = 0
            
            # Category match
            if candidate.category == article.category:
                score += 50
            
            # Tag overlap
            article_tags = set(article.tags or [])
            candidate_tags = set(candidate.tags or [])
            tag_overlap = len(article_tags & candidate_tags)
            score += tag_overlap * 10
            
            # Popularity boost
            if candidate.view_count > 10:
                score += 5
            
            recommendations.append({
                "article": candidate,
                "relevance_score": score,
                "reason": f"Related article (category: {candidate.category})"
            })
        
        # Sort and return top recommendations
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:limit]
    
    async def improve_article_with_ai(
        self,
        article: KnowledgeBaseArticle
    ) -> Dict[str, Any]:
        """
        Use AI to suggest improvements to an article
        
        Args:
            article: Article to improve
        
        Returns:
            Dict with improvement suggestions
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        
        try:
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            Analyze this knowledge base article and suggest improvements:
            
            Title: {article.title}
            Content: {article.content}
            Category: {article.category}
            
            Provide suggestions for:
            1. Clarity improvements
            2. Missing information
            3. Better structure
            4. Additional tags
            
            Return JSON format:
            {{
                "clarity_suggestions": ["suggestion1", "suggestion2"],
                "missing_info": ["info1", "info2"],
                "structure_suggestions": ["suggestion1"],
                "suggested_tags": ["tag1", "tag2"],
                "overall_score": 0.75
            }}
            """
            
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=300
            )
            
            return self._parse_improvements(response)
            
        except Exception as e:
            logger.error(f"Error in AI article improvement: {e}")
            return {
                "clarity_suggestions": [],
                "missing_info": [],
                "structure_suggestions": [],
                "suggested_tags": [],
                "overall_score": 0.0,
                "error": str(e)
            }
    
    def _parse_improvements(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI improvement suggestions"""
        import json
        import re
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Error parsing improvements: {e}")
        
        return {
            "clarity_suggestions": [],
            "missing_info": [],
            "structure_suggestions": [],
            "suggested_tags": [],
            "overall_score": 0.0
        }
    
    async def generate_answer_from_kb(
        self,
        ticket: Ticket,
        article_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered answer to a ticket using knowledge base articles
        
        This uses AI to:
        1. Find relevant KB articles
        2. Extract key information from articles
        3. Generate a personalized answer based on ticket context
        4. Provide step-by-step solution
        
        Args:
            ticket: Ticket to generate answer for
            article_id: Optional specific article to use (otherwise finds best match)
        
        Returns:
            Dict with generated answer and source articles
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        
        try:
            # Get relevant articles
            if article_id:
                article = self.db.query(KnowledgeBaseArticle).filter(
                    KnowledgeBaseArticle.id == article_id,
                    KnowledgeBaseArticle.tenant_id == self.tenant_id,
                    KnowledgeBaseArticle.status == ArticleStatus.PUBLISHED.value
                ).first()
                articles = [article] if article else []
            else:
                # Get AI suggestions
                suggestions = await self.suggest_articles_with_ai(ticket, limit=3)
                articles = [s["article"] for s in suggestions if s.get("article")]
            
            # If no KB articles, generate AI-only answer
            if not articles:
                logger.info(f"No KB articles found for ticket {ticket.id}, generating AI-only answer")
                return await self._generate_ai_only_answer(ticket)
            
            # Build context from articles
            article_context = []
            for article in articles:
                article_context.append({
                    "title": article.title,
                    "content": article.content,
                    "summary": article.summary,
                    "category": article.category
                })
            
            # Use AI to generate answer
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            You are a customer support agent. A customer has submitted a ticket and you need to provide a helpful answer.
            
            Ticket Details:
            Subject: {ticket.subject}
            Description: {ticket.description or ''}
            Type: {ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type or 'N/A'}
            Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
            
            Relevant Knowledge Base Articles:
            {chr(10).join([f"--- Article: {a['title']} ---{chr(10)}{a['content'][:500]}..." for a in article_context])}
            
            Based on the ticket and the knowledge base articles above, generate a helpful answer that:
            1. Acknowledges the customer's issue
            2. Provides a clear, step-by-step solution
            3. References specific information from the knowledge base
            4. Is professional and empathetic
            5. Includes next steps if applicable
            
            Return your answer in a clear, customer-friendly format.
            """
            
            # Call AI service
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=800
            )
            
            # Extract answer from response
            answer = response.strip() if response else None
            
            return {
                "success": True,
                "answer": answer,
                "sources": [
                    {
                        "article_id": a.id,
                        "title": a.title,
                        "relevance": "high" if i == 0 else "medium"
                    }
                    for i, a in enumerate(articles)
                ],
                "confidence": 0.85 if len(articles) > 0 else 0.5,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating answer from KB: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None,
                "sources": []
            }
    
    async def generate_quick_response(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Generate a quick response template based on KB articles
        
        This is faster than full answer generation and provides a template
        that agents can customize.
        
        Args:
            ticket: Ticket to generate response for
        
        Returns:
            Dict with response template
        """
        try:
            # Get top article suggestion
            suggestions = await self.suggest_articles_with_ai(ticket, limit=1)
            
            if not suggestions:
                # Generate AI-only quick response if no KB articles
                logger.info(f"No KB articles found for ticket {ticket.id}, generating AI-only quick response")
                return await self._generate_ai_only_quick_response(ticket)
            
            article = suggestions[0]["article"]
            
            # Create template from article
            template = f"""
            Thank you for contacting us regarding: {ticket.subject}
            
            Based on our knowledge base, here's a solution:
            
            {article.summary or article.content[:300]}
            
            For more details, please see: {article.title}
            
            If this doesn't resolve your issue, please let us know and we'll investigate further.
            """
            
            return {
                "success": True,
                "template": template.strip(),
                "article": {
                    "id": article.id,
                    "title": article.title,
                    "url": f"/knowledge-base/articles/{article.id}"
                }
            }
        except Exception as e:
            logger.error(f"Error in generate_quick_response: {e}", exc_info=True)
            self.db.rollback()
            # Fallback to AI-only response on error
            try:
                return await self._generate_ai_only_quick_response(ticket)
            except Exception as fallback_error:
                logger.error(f"Error in fallback AI-only response: {fallback_error}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "template": None,
                    "article": None
                }
    
    async def _generate_ai_only_answer(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered answer without KB articles
        
        This is a fallback when no KB articles are available.
        Uses AI to generate a helpful response based on ticket context.
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        from app.models.crm import Customer
        
        try:
            # Get customer context if available
            customer_context = ""
            if ticket.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == ticket.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
                if customer:
                    customer_context = f"\nCustomer: {customer.company_name or customer.main_email}"
            
            # Use AI to generate answer
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            You are a customer support agent. A customer has submitted a ticket and you need to provide a helpful answer.
            
            Ticket Details:
            Subject: {ticket.subject}
            Description: {ticket.description or ''}
            Type: {ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type or 'N/A'}
            Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
            {customer_context}
            
            Note: No knowledge base articles are available for this ticket. Generate a helpful, professional answer based on:
            1. Your understanding of common support issues
            2. Best practices for customer service
            3. The specific details of this ticket
            
            Generate a helpful answer that:
            1. Acknowledges the customer's issue with empathy
            2. Provides a clear, step-by-step solution or guidance
            3. Is professional and customer-friendly
            4. Includes next steps if applicable
            5. Offers to help further if needed
            
            Return your answer in a clear, customer-friendly format.
            """
            
            # Call AI service
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=800
            )
            
            # Extract answer from response
            answer = response.strip() if response else None
            
            return {
                "success": True,
                "answer": answer,
                "sources": [],
                "confidence": 0.7,  # Lower confidence when no KB articles
                "generated_at": datetime.now().isoformat(),
                "ai_only": True  # Flag to indicate this was AI-only
            }
            
        except Exception as e:
            logger.error(f"Error generating AI-only answer: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None,
                "sources": []
            }
    
    async def _generate_ai_only_quick_response(
        self,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Generate a quick response template without KB articles
        
        This is a fallback when no KB articles are available.
        """
        from app.services.ai_orchestration_service import AIOrchestrationService
        from app.models.ai_prompt import PromptCategory
        from app.models.crm import Customer
        
        try:
            # Get customer context if available
            customer_context = ""
            if ticket.customer_id:
                customer = self.db.query(Customer).filter(
                    Customer.id == ticket.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
                if customer:
                    customer_context = f"\nCustomer: {customer.company_name or customer.main_email}"
            
            # Use AI to generate quick response
            ai_service = AIOrchestrationService(self.db, self.tenant_id)
            
            prompt_text = f"""
            Generate a professional, empathetic quick response template for a customer support ticket.
            
            Ticket Details:
            Subject: {ticket.subject}
            Description: {ticket.description or ''}
            Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
            {customer_context}
            
            Create a brief, professional response template that:
            1. Acknowledges the customer's issue
            2. Shows empathy and understanding
            3. Provides initial guidance or next steps
            4. Is ready to customize with specific details
            
            Keep it concise (2-3 sentences) and professional.
            """
            
            response = await ai_service.generate_response(
                prompt_text=prompt_text,
                category=PromptCategory.CUSTOMER_SERVICE.value,
                max_tokens=200
            )
            
            template = response.strip() if response else None
            
            return {
                "success": True,
                "template": template,
                "article": None,
                "ai_only": True  # Flag to indicate this was AI-only
            }
            
        except Exception as e:
            logger.error(f"Error generating AI-only quick response: {e}")
            return {
                "success": False,
                "template": None,
                "article": None
            }


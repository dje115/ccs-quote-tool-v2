#!/usr/bin/env python3
"""
Ticket Agent Assistant Service
Allows agents to have conversations with AI about tickets, with support for attachments and log files
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.core.database import SessionLocal
from app.models.helpdesk import Ticket, TicketComment, TicketAttachment
from app.models.crm import Customer
from app.models.ai_prompt import PromptCategory
from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService


class TicketAgentAssistantService:
    """Service for agent chatbot conversations about tickets"""

    def __init__(self, db: Session, tenant_id: str):
        # Note: db parameter is kept for compatibility but not used - each method creates its own session
        self.tenant_id = tenant_id

    async def _load_ticket_context(self, ticket_id: str) -> Dict[str, Any]:
        """Load full ticket context for the AI"""
        from app.models.helpdesk import Ticket, TicketComment, TicketHistory, NPAHistory, TicketAttachment
        from app.services.storage_service import get_storage_service
        
        sync_db = SessionLocal()
        try:
            ticket = sync_db.query(Ticket).filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id
            ).first()
            
            if not ticket:
                raise ValueError("Ticket not found")
            
            # Get customer info
            customer = None
            if ticket.customer_id:
                customer = sync_db.query(Customer).filter(
                    Customer.id == ticket.customer_id,
                    Customer.tenant_id == self.tenant_id
                ).first()
            
            # Get comments
            comments = sync_db.query(TicketComment).filter(
                TicketComment.ticket_id == ticket_id
            ).order_by(TicketComment.created_at).all()
            
            # Get NPA history
            npa_history = sync_db.query(NPAHistory).filter(
                NPAHistory.ticket_id == ticket_id,
                NPAHistory.tenant_id == self.tenant_id
            ).order_by(NPAHistory.created_at).all()
            
            # Get ticket attachments
            ticket_attachments = sync_db.query(TicketAttachment).filter(
                TicketAttachment.ticket_id == ticket_id,
                TicketAttachment.comment_id.is_(None)  # Only ticket-level attachments, not comment attachments
            ).all()
            
            # Build context
            context_parts = []
            context_parts.append(f"=== TICKET INFORMATION ===")
            context_parts.append(f"Ticket Number: {ticket.ticket_number}")
            context_parts.append(f"Subject: {ticket.subject}")
            context_parts.append(f"Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}")
            context_parts.append(f"Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}")
            context_parts.append(f"Type: {ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type}")
            
            if customer:
                context_parts.append(f"\n=== CUSTOMER INFORMATION ===")
                context_parts.append(f"Company: {customer.company_name}")
                if customer.description:
                    context_parts.append(f"Description: {customer.description[:500]}")
            
            context_parts.append(f"\n=== TICKET DESCRIPTION ===")
            context_parts.append(ticket.description or "No description provided")
            
            if ticket.original_description and ticket.original_description != ticket.description:
                context_parts.append(f"\n=== ORIGINAL DESCRIPTION (Agent Notes) ===")
                context_parts.append(ticket.original_description)
            
            if ticket.cleaned_description:
                context_parts.append(f"\n=== CLEANED DESCRIPTION (Customer-Facing) ===")
                context_parts.append(ticket.cleaned_description)
            
            # Add NPA information
            if ticket.npa_original_text:
                context_parts.append(f"\n=== NEXT POINT OF ACTION ===")
                context_parts.append(f"State: {ticket.npa_state or 'N/A'}")
                context_parts.append(f"Original: {ticket.npa_original_text}")
                if ticket.npa_cleaned_text:
                    context_parts.append(f"Cleaned: {ticket.npa_cleaned_text}")
                if ticket.npa_answers_original_text:
                    context_parts.append(f"Answers to Questions: {ticket.npa_answers_original_text}")
            
            # Add NPA history
            if npa_history:
                context_parts.append(f"\n=== NPA HISTORY ===")
                for idx, npa in enumerate(npa_history, 1):
                    context_parts.append(f"\nNPA #{idx} ({npa.npa_state or 'N/A'}):")
                    context_parts.append(npa.npa_original_text or '')
                    if npa.answers_to_questions:
                        context_parts.append(f"Answers: {npa.answers_to_questions}")
            
            # Add comments
            if comments:
                context_parts.append(f"\n=== COMMENTS ===")
                for comment in comments:
                    author = comment.author_name or comment.author_email or 'System'
                    internal = " (Internal)" if comment.is_internal else ""
                    context_parts.append(f"\n{author}{internal} - {comment.created_at.strftime('%Y-%m-%d %H:%M')}:")
                    context_parts.append(comment.comment)
            
            # Add AI suggestions if available
            if ticket.ai_suggestions:
                context_parts.append(f"\n=== AI SUGGESTIONS ===")
                suggestions = ticket.ai_suggestions if isinstance(ticket.ai_suggestions, dict) else {}
                if suggestions.get('next_actions'):
                    context_parts.append(f"Next Actions: {', '.join(suggestions['next_actions'])}")
                if suggestions.get('questions'):
                    context_parts.append(f"Questions to Ask: {', '.join(suggestions['questions'])}")
                if suggestions.get('solutions'):
                    context_parts.append(f"Potential Solutions: {', '.join(suggestions['solutions'])}")
            
            # Add ticket attachments
            if ticket_attachments:
                context_parts.append(f"\n=== TICKET ATTACHMENTS ===")
                storage_service = get_storage_service()
                
                for att in ticket_attachments:
                    context_parts.append(f"\nAttachment: {att.filename}")
                    context_parts.append(f"Size: {att.file_size} bytes")
                    if att.content_type:
                        context_parts.append(f"Type: {att.content_type}")
                    
                    # Try to read text-based attachments for context
                    try:
                        # Only read text-based files (limit to reasonable size: 100KB)
                        text_extensions = ['.txt', '.log', '.json', '.xml', '.csv', '.md', '.py', '.js', '.html', '.css', '.conf', '.config']
                        if att.file_size < 100 * 1024 and any(att.filename.lower().endswith(ext) for ext in text_extensions):
                            file_data = await storage_service.download_file(att.file_path)
                            # Decode as text (try UTF-8, fallback to latin-1)
                            try:
                                file_content = file_data.decode('utf-8')
                            except UnicodeDecodeError:
                                file_content = file_data.decode('latin-1', errors='ignore')
                            
                            # Limit content size for context
                            max_content_length = 5000
                            if len(file_content) > max_content_length:
                                file_content = file_content[:max_content_length] + f"\n... (truncated, total {len(file_content)} chars)"
                            
                            context_parts.append(f"Content:\n{file_content}")
                        else:
                            context_parts.append(f"(Binary file - {att.file_size} bytes)")
                    except Exception as e:
                        # If we can't read the file, just note it exists
                        context_parts.append(f"(File exists but could not be read: {str(e)})")
            
            return {
                "ticket": ticket,
                "customer": customer,
                "context": "\n".join(context_parts)
            }
        finally:
            sync_db.close()

    async def chat(
        self,
        ticket_id: str,
        messages: List[Dict[str, str]],
        attachments: Optional[List[Dict[str, Any]]] = None,
        log_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Have a conversation with AI about a ticket
        
        Args:
            ticket_id: Ticket ID
            messages: List of {role: 'user'|'assistant', content: '...'}
            attachments: Optional list of attachment info {filename, content, type}
            log_files: Optional list of log file contents (as strings)
        
        Returns:
            AI response with message and context
        """
        # Load ticket context
        ticket_data = await self._load_ticket_context(ticket_id)
        context_block = ticket_data["context"]
        
        # Add attachments and log files to context if provided
        if attachments:
            context_block += "\n\n=== ATTACHMENTS ==="
            for att in attachments:
                context_block += f"\n{att.get('filename', 'attachment')}: {att.get('content', '')[:2000]}"
        
        if log_files:
            context_block += "\n\n=== LOG FILES ==="
            for idx, log_content in enumerate(log_files, 1):
                context_block += f"\n\nLog File {idx}:\n{log_content[:5000]}"  # Limit log size
        
        # Build conversation prompt
        conversation_snippets = [f"[TICKET CONTEXT]\n{context_block}\n"]
        for msg in messages:
            role = msg.get("role", "user").upper()
            conversation_snippets.append(f"{role}: {msg.get('content', '')}")
        user_prompt = "\n\n".join(conversation_snippets)
        
        sync_db = SessionLocal()
        try:
            prompt_service = AIPromptService(sync_db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                PromptCategory.HELPDESK_AGENT_ASSISTANT.value,
                tenant_id=self.tenant_id
            )
            
            if not prompt_obj:
                # Fallback system prompt if not in database
                system_prompt = """You are a helpful support agent assistant. You help agents understand tickets, diagnose issues, suggest solutions, and answer questions about ticket details. You have access to the full ticket context including description, comments, NPA history, and customer information. Be concise, helpful, and actionable in your responses."""
            else:
                system_prompt = prompt_obj.system_prompt
            
            ai_service = AIProviderService(sync_db, self.tenant_id)
            ai_response = await ai_service.generate_with_rendered_prompts(
                prompt=prompt_obj,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=prompt_obj.model if prompt_obj else "gpt-5-mini",
                temperature=0.7,
                max_tokens=prompt_obj.max_tokens if prompt_obj else 2000,
                use_responses_api=False
            )
            
            return {
                "message": ai_response.content,
                "model": ai_response.model,
                "usage": ai_response.usage,
                "context": context_block[:500]  # Return truncated context for reference
            }
        finally:
            sync_db.close()


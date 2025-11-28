import json
from sqlalchemy import desc
from app.core.database import SessionLocal
from app.models.quotes import Quote
from app.models.helpdesk import Ticket

CUSTOMER_ID = '161f01e2-f1e5-4b08-942d-8b75aac95ba0'
TENANT_ID = '1dcb3c53-1763-43a9-98d0-b37241728dc2'

session = SessionLocal()
quotes = session.query(Quote).filter(
    Quote.customer_id == CUSTOMER_ID,
    Quote.tenant_id == TENANT_ID,
    Quote.is_deleted == False
).order_by(desc(Quote.created_at)).limit(5).all()
print(f"Quotes found: {len(quotes)}")
for q in quotes:
    status_value = getattr(q.status, 'value', q.status)
    print(f"- {q.quote_number} ({status_value}) | title={q.title} | total={q.total_amount}")

quote_summary = ''
if quotes:
    quote_summary = 'Quote Pipeline:\n'
    for q in quotes:
        status_value = getattr(q.status, 'value', q.status)
        total_value = float(q.total_amount or 0)
        title = (q.title or '')[:60]
        quote_summary += f"- {q.quote_number} ({status_value}) GBP{total_value:,.0f} - {title}\n"
print('\nQuote summary block:\n' + quote_summary)

tickets = session.query(Ticket).filter(
    Ticket.customer_id == CUSTOMER_ID,
    Ticket.tenant_id == TENANT_ID
).order_by(desc(Ticket.created_at)).limit(5).all()
print(f"\nTickets found: {len(tickets)}")
for t in tickets:
    status_value = getattr(t.status, 'value', t.status)
    priority_value = getattr(t.priority, 'value', t.priority)
    print(f"- {t.ticket_number} [{priority_value}/{status_value}] | subject={t.subject}")

if tickets:
    ticket_summary = 'Support Tickets:\n'
    for t in tickets:
        status_value = getattr(t.status, 'value', t.status)
        priority_value = getattr(t.priority, 'value', t.priority)
        subject = (t.subject or '')[:70]
        ticket_summary += f"- {t.ticket_number} [{priority_value}/{status_value}] {subject}\n"
    print('\nTicket summary block:\n' + ticket_summary)

session.close()

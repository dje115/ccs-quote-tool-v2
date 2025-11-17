-- Seed Customer Service / Ticket Analysis AI Prompt
-- This prompt is used to analyze support tickets and improve descriptions with AI suggestions

INSERT INTO ai_prompts (
    id,
    name,
    category,
    description,
    system_prompt,
    user_prompt_template,
    model,
    temperature,
    max_tokens,
    is_active,
    is_system,
    tenant_id,
    created_by,
    variables,
    version,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid()::text,
    'Customer Service - Ticket Analysis',
    'customer_service',
    'Analyze support tickets to improve descriptions and suggest next actions, questions, and solutions',
    'You are a customer service assistant specializing in analyzing support tickets. You improve ticket descriptions to be professional and customer-friendly, and provide actionable suggestions for resolving customer issues. Always respond with valid JSON matching the required format.',
    'You are a customer service assistant. Analyze the following support ticket and:

1. Improve the description to be clear, professional, and customer-friendly (this will be shown to the customer)
2. Suggest next actions/questions that should be asked to gather more information
3. Suggest potential solutions if enough information is available

Original Ticket:
Subject: {ticket_subject}
Description: {ticket_description}
{customer_context}

IMPORTANT GUIDELINES:
- The improved description should be professional, clear, and customer-facing
- Keep all factual information from the original description
- Make it concise but complete
- Use proper grammar and professional language
- The improved description will be shown to the customer in the portal
- Preserve the original description for internal reference

SUGGESTIONS GUIDELINES:
- Next actions should be specific and actionable (e.g., "Ask customer for error logs" not "Gather more info")
- Questions should help diagnose the issue or gather necessary details
- Solutions should be practical and based on the information provided
- If insufficient information is available, focus on questions and next actions rather than solutions

Provide your response in JSON format:
{{
    "improved_description": "The improved, professional description that will be shown to the customer",
    "suggestions": {{
        "next_actions": [
            "Specific action 1 (e.g., ''Request error logs from customer'')",
            "Specific action 2 (e.g., ''Check system logs for timestamp'')"
        ],
        "questions": [
            "Question 1 to gather more information (e.g., ''What error message appears when this happens?'')",
            "Question 2 to diagnose the issue (e.g., ''Does this happen on all devices or just one?'')"
        ],
        "solutions": [
            "Potential solution 1 if enough info is available (e.g., ''Reset password and clear cache'')",
            "Potential solution 2 if applicable (e.g., ''Update to latest version'')"
        ]
    }}
}}

If you cannot provide solutions due to insufficient information, return an empty array for "solutions" but always provide "next_actions" and "questions".',
    'gpt-5-mini',
    0.7,
    2000,
    true,
    true,
    NULL,
    NULL,
    '{"ticket_subject": "Ticket subject line", "ticket_description": "Original ticket description from agent", "customer_context": "Customer information including company name, business sector, and description (optional)"}'::jsonb,
    1,
    NOW(),
    NOW()
)
ON CONFLICT DO NOTHING;

-- Verify the prompt was created
SELECT id, name, category, is_active, is_system 
FROM ai_prompts 
WHERE category = 'customer_service' 
AND is_system = true;


#!/usr/bin/env python3
"""Check detailed AI analysis data for Alliance Tooling"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.leads import Lead
import json

db = SessionLocal()

lead = db.query(Lead).filter(Lead.company_name.ilike('%Alliance Tooling%')).first()

if not lead:
    print("Discovery not found")
    sys.exit(1)

print("=" * 80)
print("ALLIANCE TOOLING LTD - DETAILED AI ANALYSIS DATA")
print("=" * 80)

print(f"\nCompany: {lead.company_name}")
print(f"Lead Score: {lead.lead_score}")
print(f"Qualification Reason: {lead.qualification_reason[:200] if lead.qualification_reason else 'N/A'}...")

print("\n" + "=" * 80)
print("AI ANALYSIS DATA (Full Structure)")
print("=" * 80)

if lead.ai_analysis:
    if isinstance(lead.ai_analysis, dict):
        print(f"\nAI Analysis Type: dict")
        print(f"Total Keys: {len(lead.ai_analysis.keys())}")
        print(f"Keys: {list(lead.ai_analysis.keys())}")
        
        # Check each key
        for key in lead.ai_analysis.keys():
            value = lead.ai_analysis[key]
            if isinstance(value, (list, dict)):
                print(f"\n  {key}:")
                if isinstance(value, list):
                    print(f"    Type: list, Length: {len(value)}")
                    if len(value) > 0:
                        print(f"    First item type: {type(value[0])}")
                        if isinstance(value[0], str):
                            print(f"    First item preview: {value[0][:100]}...")
                elif isinstance(value, dict):
                    print(f"    Type: dict, Keys: {list(value.keys())[:10]}")
            elif isinstance(value, str):
                print(f"\n  {key}:")
                print(f"    Type: str, Length: {len(value)}")
                print(f"    Preview: {value[:200]}...")
            else:
                print(f"\n  {key}: {type(value)} = {value}")
        
        # Check for similar companies specifically
        if 'similar_companies' in lead.ai_analysis:
            print(f"\n  SIMILAR COMPANIES FOUND:")
            similar = lead.ai_analysis['similar_companies']
            if isinstance(similar, list):
                print(f"    Count: {len(similar)}")
                for i, company in enumerate(similar[:5], 1):
                    if isinstance(company, dict):
                        print(f"    {i}. {company.get('company_name', 'N/A')} - {company.get('similarity_score', 'N/A')}%")
                    else:
                        print(f"    {i}. {company}")
        else:
            print("\n  ⚠️  No 'similar_companies' key found in AI analysis")
            
        # Check opportunity_summary
        if 'opportunity_summary' in lead.ai_analysis:
            opp = lead.ai_analysis['opportunity_summary']
            print(f"\n  OPPORTUNITY SUMMARY:")
            if isinstance(opp, str):
                print(f"    Length: {len(opp)} chars")
                print(f"    Preview: {opp[:300]}...")
        
        # Check recommendations
        if 'recommendations' in lead.ai_analysis:
            recs = lead.ai_analysis['recommendations']
            print(f"\n  RECOMMENDATIONS:")
            if isinstance(recs, list):
                print(f"    Count: {len(recs)}")
                for i, rec in enumerate(recs[:3], 1):
                    print(f"    {i}. {rec[:100]}...")
        
        # Check next_steps
        if 'next_steps' in lead.ai_analysis:
            steps = lead.ai_analysis['next_steps']
            print(f"\n  NEXT STEPS:")
            if isinstance(steps, list):
                print(f"    Count: {len(steps)}")
                for i, step in enumerate(steps[:3], 1):
                    print(f"    {i}. {step[:100]}...")
                    
    else:
        print(f"AI Analysis Type: {type(lead.ai_analysis)}")
        print(f"Content: {str(lead.ai_analysis)[:500]}...")
else:
    print("❌ No AI analysis data found")

print("\n" + "=" * 80)
print("OTHER AI FIELDS")
print("=" * 80)
print(f"AI Confidence Score: {lead.ai_confidence_score}")
print(f"AI Recommendation: {lead.ai_recommendation[:200] if lead.ai_recommendation else 'N/A'}...")
print(f"AI Notes: {lead.ai_notes[:200] if lead.ai_notes else 'N/A'}...")

db.close()


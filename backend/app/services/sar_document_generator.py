#!/usr/bin/env python3
"""
SAR Document Generator Service
Generates PDF documents for Subject Access Request (SAR) exports
"""

import logging
from io import BytesIO
from typing import Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

logger = logging.getLogger(__name__)


class SARDocumentGenerator:
    """Service for generating GDPR-compliant SAR PDF documents"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for SAR document"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='SARTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='SARHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=12
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='SARSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=6,
            spaceBefore=8
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='SARBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='SARFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        ))
    
    def generate_pdf(self, sar_data: Dict[str, Any]) -> BytesIO:
        """
        Generate a GDPR-compliant SAR PDF document
        
        Args:
            sar_data: Dictionary containing SAR report data
            
        Returns:
            BytesIO object containing the PDF document
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        story.append(Paragraph(sar_data.get('report_type', 'Subject Access Request (SAR) Response Report'), self.styles['SARTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Company and reference
        company = sar_data.get('company', 'CCS Quote Tool')
        reference = sar_data.get('reference', 'N/A')
        date_response = sar_data.get('date_of_response', datetime.now().isoformat())
        
        info_data = [
            ['Company:', company],
            ['Reference:', reference],
            ['Date of Response:', self._format_date(date_response)]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Introduction
        introduction = sar_data.get('introduction', '')
        if introduction:
            story.append(Paragraph('1. Introduction', self.styles['SARHeading']))
            story.append(Paragraph(introduction, self.styles['SARBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Data Subject Information
        data_subject = sar_data.get('data_subject', {})
        if data_subject:
            story.append(Paragraph('2. Data Subject Information', self.styles['SARHeading']))
            subject_info = [
                ['Name:', data_subject.get('name', 'N/A')],
                ['Email:', data_subject.get('email', 'N/A') or 'N/A'],
                ['Phone:', data_subject.get('phone', 'N/A') or 'N/A'],
                ['Role:', data_subject.get('role', 'N/A') or 'N/A'],
                ['Company:', data_subject.get('company', 'N/A') or 'N/A']
            ]
            subject_table = Table(subject_info, colWidths=[2*inch, 4*inch])
            subject_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(subject_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Categories of Personal Data
        categories = sar_data.get('categories_of_personal_data', {})
        if categories:
            story.append(Paragraph('3. Categories of Personal Data Held', self.styles['SARHeading']))
            
            contact_info = categories.get('contact_information', {})
            if contact_info:
                story.append(Paragraph('3.1 Contact Information', self.styles['SARSubheading']))
                contact_data = [
                    ['Full Name:', contact_info.get('full_name', 'N/A')],
                    ['Job Title/Role:', contact_info.get('job_title_role', 'N/A') or 'N/A'],
                    ['Work Email:', contact_info.get('work_email_address', 'N/A') or 'N/A'],
                    ['Work Telephone:', contact_info.get('work_telephone', 'N/A') or 'N/A'],
                    ['Company Address:', contact_info.get('company_address', 'N/A') or 'N/A']
                ]
                contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
                contact_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(contact_table)
                story.append(Spacer(1, 0.15*inch))
        
        # Communications
        data = sar_data.get('data', {})
        communications = data.get('communications', [])
        if communications:
            story.append(Paragraph('3.2 Communications', self.styles['SARSubheading']))
            story.append(Paragraph(
                f'We hold {len(communications)} communication record(s) relating to you. '
                'These include support tickets, emails, and activity notes. '
                'Only AI-cleaned, customer-facing versions are included in this report. '
                'Internal notes and references to other individuals have been redacted.',
                self.styles['SARBody']
            ))
            
            # Show first few communications as examples
            for i, comm in enumerate(communications[:5], 1):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f'<b>Communication {i}:</b> {comm.get("type", "N/A")}', self.styles['SARSubheading']))
                if comm.get('subject'):
                    story.append(Paragraph(f'<b>Subject:</b> {comm.get("subject")}', self.styles['SARBody']))
                if comm.get('date'):
                    story.append(Paragraph(f'<b>Date:</b> {self._format_date(comm.get("date"))}', self.styles['SARBody']))
                if comm.get('description') or comm.get('notes'):
                    content = comm.get('description') or comm.get('notes', '')
                    if content:
                        # Truncate long content
                        if len(content) > 500:
                            content = content[:500] + '... [Content truncated for brevity]'
                        story.append(Paragraph(f'<b>Content:</b> {content}', self.styles['SARBody']))
            
            if len(communications) > 5:
                story.append(Paragraph(
                    f'<i>... and {len(communications) - 5} more communication record(s). '
                    'Full details are available in the digital export.</i>',
                    self.styles['SARBody']
                ))
            story.append(Spacer(1, 0.2*inch))
        
        # Contracts and Accounts
        contracts = data.get('contracts_and_accounts', [])
        if contracts:
            story.append(Paragraph('3.3 Contract and Account Data', self.styles['SARSubheading']))
            story.append(Paragraph(
                f'We hold {len(contracts)} contract/account record(s) relating to you.',
                self.styles['SARBody']
            ))
            story.append(Spacer(1, 0.1*inch))
        
        # Source of Data
        source_of_data = sar_data.get('source_of_data', [])
        if source_of_data:
            story.append(PageBreak())
            story.append(Paragraph('4. Source of the Personal Data', self.styles['SARHeading']))
            story.append(Paragraph(
                'Data has been obtained from the following sources:',
                self.styles['SARBody']
            ))
            for source in source_of_data:
                story.append(Paragraph(f'• {source}', self.styles['SARBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Purpose and Lawful Basis
        purpose_basis = sar_data.get('purpose_and_lawful_basis', {})
        if purpose_basis:
            story.append(Paragraph('5. Purpose and Lawful Basis for Processing', self.styles['SARHeading']))
            
            purpose_data = [['Purpose', 'Lawful Basis', 'Details']]
            for key, value in purpose_basis.items():
                if isinstance(value, dict):
                    purpose_data.append([
                        value.get('purpose', 'N/A'),
                        value.get('lawful_basis', 'N/A'),
                        value.get('details', 'N/A')
                    ])
            
            purpose_table = Table(purpose_data, colWidths=[2*inch, 2*inch, 2*inch])
            purpose_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            story.append(purpose_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Retention Periods
        retention = sar_data.get('retention_periods', {})
        if retention:
            story.append(Paragraph('6. Retention Periods', self.styles['SARHeading']))
            retention_data = [['Data Type', 'Retention Period']]
            for data_type, period in retention.items():
                retention_data.append([
                    data_type.replace('_', ' ').title(),
                    period
                ])
            
            retention_table = Table(retention_data, colWidths=[3*inch, 3*inch])
            retention_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            story.append(retention_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Data Subject Rights
        rights = sar_data.get('data_subject_rights', {})
        if rights:
            story.append(Paragraph('7. Your Rights Under GDPR', self.styles['SARHeading']))
            story.append(Paragraph(
                'Individuals have the following rights under GDPR:',
                self.styles['SARBody']
            ))
            for key, value in rights.items():
                right_name = key.replace('_', ' ').replace('right to ', '').title()
                story.append(Paragraph(f'• <b>{right_name}:</b> {value}', self.styles['SARBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f'This document was generated on {self._format_date(datetime.now().isoformat())}. '
            'This is a summary document. Full data export is available in digital format.',
            self.styles['SARFooter']
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _format_date(self, date_str: str) -> str:
        """Format ISO date string to readable format"""
        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%d %B %Y')
            return str(date_str)
        except:
            return str(date_str)


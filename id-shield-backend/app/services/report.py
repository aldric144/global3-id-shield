import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.models.report import Report, ReportType, ReportStatus
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.analysis import AnalysisResult, AnalysisStatus, ConfidenceTier
from app.models.user import User
from app.utils.hashing import compute_string_hash
from app.utils.audit import create_audit_log
from app.models.audit import AuditAction
from app.config import settings


class ReportService:
    """
    Court-Ready Forensic Report Generation Service
    
    Generates PDF reports that are:
    - Explainable
    - Neutral in tone
    - Reproducible
    - Include chain-of-custody documentation
    """
    
    @staticmethod
    def generate_report_number(case_number: str, sequence: int) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"{case_number}-RPT-{timestamp}-{sequence:03d}"
    
    @staticmethod
    async def create_forensic_report(
        db: AsyncSession,
        case_id: int,
        report_type: ReportType,
        title: str,
        user: User,
        evidence_ids: Optional[List[int]] = None,
        ip_address: Optional[str] = None
    ) -> Report:
        """Generate a court-ready forensic report."""
        
        case_result = await db.execute(select(Case).where(Case.id == case_id))
        case = case_result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
        if case.agency_id != user.agency_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        if evidence_ids:
            evidence_result = await db.execute(
                select(Evidence).where(
                    Evidence.id.in_(evidence_ids),
                    Evidence.case_id == case_id
                )
            )
            evidence_items = list(evidence_result.scalars().all())
        else:
            evidence_result = await db.execute(
                select(Evidence).where(Evidence.case_id == case_id)
            )
            evidence_items = list(evidence_result.scalars().all())
        
        analysis_results = []
        for ev in evidence_items:
            ar_result = await db.execute(
                select(AnalysisResult).where(AnalysisResult.evidence_id == ev.id)
            )
            analysis_results.extend(ar_result.scalars().all())
        
        existing_count = await db.execute(
            select(Report).where(Report.case_id == case_id)
        )
        sequence = len(list(existing_count.scalars().all())) + 1
        report_number = ReportService.generate_report_number(case.case_number, sequence)
        
        report = Report(
            report_number=report_number,
            case_id=case_id,
            generated_by=user.id,
            report_type=report_type,
            title=title,
            status=ReportStatus.GENERATING,
            included_evidence_ids=[ev.id for ev in evidence_items],
            included_analysis_ids=[ar.id for ar in analysis_results]
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        await create_audit_log(
            db=db,
            action=AuditAction.REPORT_GENERATE,
            user_id=user.id,
            agency_id=user.agency_id,
            resource_type="report",
            resource_id=report.id,
            resource_uuid=report.uuid,
            ip_address=ip_address,
            details={
                "case_id": case_id,
                "report_type": report_type.value,
                "evidence_count": len(evidence_items)
            }
        )
        
        try:
            file_path = await ReportService._generate_pdf(
                report, case, evidence_items, analysis_results, user
            )
            
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = compute_string_hash(content.hex())
            
            report.file_path = file_path
            report.file_hash = file_hash
            report.status = ReportStatus.COMPLETED
            
            summary, limitations = ReportService._generate_summary(analysis_results)
            report.summary = summary
            report.limitations_section = limitations
            
            await db.commit()
            await db.refresh(report)
            
        except Exception as e:
            report.status = ReportStatus.FAILED
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}"
            )
        
        return report
    
    @staticmethod
    async def _generate_pdf(
        report: Report,
        case: Case,
        evidence_items: List[Evidence],
        analysis_results: List[AnalysisResult],
        user: User
    ) -> str:
        """Generate the actual PDF document."""
        
        os.makedirs(settings.reports_dir, exist_ok=True)
        filename = f"{report.report_number}.pdf"
        file_path = os.path.join(settings.reports_dir, filename)
        
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a365d')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor('#4a5568')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        )
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER,
            spaceBefore=20
        )
        
        story = []
        
        story.append(Paragraph("GLOBAL3 TECHNOLOGY & INTELLIGENCE", disclaimer_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("ID SHIELD™ FORENSIC ANALYSIS REPORT", title_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Report Number: {report.report_number}", body_style))
        story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("CASE INFORMATION", heading_style))
        case_data = [
            ["Case Number:", case.case_number],
            ["Case Title:", case.title],
            ["Case Type:", case.case_type],
            ["Status:", case.status.value.upper()],
            ["Priority:", case.priority.value.upper()],
            ["Created:", case.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if case.created_at else "N/A"],
        ]
        if case.incident_date:
            case_data.append(["Incident Date:", case.incident_date.strftime('%Y-%m-%d')])
        if case.incident_location:
            case_data.append(["Incident Location:", case.incident_location])
        
        case_table = Table(case_data, colWidths=[1.5*inch, 5*inch])
        case_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(case_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("EVIDENCE INVENTORY", heading_style))
        
        for ev in evidence_items:
            story.append(Paragraph(f"Evidence: {ev.evidence_number}", subheading_style))
            ev_data = [
                ["Original Filename:", ev.original_filename],
                ["Type:", ev.evidence_type.value.upper()],
                ["File Size:", f"{ev.file_size:,} bytes"],
                ["SHA-256 Hash:", ev.sha256_hash],
                ["MD5 Hash:", ev.md5_hash],
                ["Upload Date:", ev.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if ev.created_at else "N/A"],
                ["Status:", ev.status.value.upper()],
            ]
            if ev.quality_score is not None:
                ev_data.append(["Quality Score:", f"{ev.quality_score}/100"])
            
            ev_table = Table(ev_data, colWidths=[1.5*inch, 5*inch])
            ev_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(ev_table)
            story.append(Spacer(1, 10))
        
        story.append(PageBreak())
        
        story.append(Paragraph("ANALYSIS RESULTS", heading_style))
        
        evidence_analysis_map = {}
        for ar in analysis_results:
            if ar.evidence_id not in evidence_analysis_map:
                evidence_analysis_map[ar.evidence_id] = []
            evidence_analysis_map[ar.evidence_id].append(ar)
        
        for ev in evidence_items:
            story.append(Paragraph(f"Analysis for Evidence: {ev.evidence_number}", subheading_style))
            
            ev_analyses = evidence_analysis_map.get(ev.id, [])
            
            if not ev_analyses:
                story.append(Paragraph("No analysis results available for this evidence.", body_style))
                continue
            
            for ar in ev_analyses:
                analysis_name = ar.analysis_type.value.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{analysis_name}</b>", body_style))
                
                status_text = ar.status.value.upper()
                if ar.confidence_tier:
                    status_text += f" | Confidence: {ar.confidence_tier.value.upper()}"
                if ar.confidence_score:
                    status_text += f" ({ar.confidence_score:.1f}%)"
                story.append(Paragraph(f"Status: {status_text}", body_style))
                
                if ar.summary:
                    story.append(Paragraph(f"Summary: {ar.summary}", body_style))
                
                if ar.warnings:
                    warnings_text = "Warnings: " + "; ".join(ar.warnings)
                    story.append(Paragraph(f"<font color='#c53030'>{warnings_text}</font>", body_style))
                
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 15))
        
        story.append(PageBreak())
        
        story.append(Paragraph("LIMITATIONS AND DISCLAIMERS", heading_style))
        
        all_limitations = set()
        for ar in analysis_results:
            if ar.limitations:
                all_limitations.update(ar.limitations)
        
        if all_limitations:
            for limitation in all_limitations:
                story.append(Paragraph(f"• {limitation}", body_style))
        else:
            story.append(Paragraph("No specific limitations noted.", body_style))
        
        story.append(Spacer(1, 15))
        
        standard_disclaimers = [
            "This report presents forensic analysis results and does not constitute legal advice.",
            "Confidence scores represent algorithmic assessments and should be interpreted by qualified experts.",
            "The system assesses evidence consistency and authenticity indicators; it does not make guilt or innocence determinations.",
            "All analysis is based on evidence as provided; the system cannot verify original source authenticity.",
            "Results should be considered alongside other investigative findings and expert testimony."
        ]
        
        for disclaimer in standard_disclaimers:
            story.append(Paragraph(f"• {disclaimer}", body_style))
        
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("CERTIFICATION", heading_style))
        story.append(Paragraph(
            f"This report was generated by ID SHIELD™ forensic analysis platform on "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d at %H:%M:%S UTC')}. "
            f"Report generated by user ID {user.id} ({user.email}).",
            body_style
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Report Number: {report.report_number}",
            body_style
        ))
        story.append(Paragraph(
            f"System Version: 1.0.0-MVP",
            body_style
        ))
        
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "— END OF REPORT —",
            ParagraphStyle('EndMarker', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)
        ))
        
        doc.build(story)
        
        return file_path
    
    @staticmethod
    def _generate_summary(analysis_results: List[AnalysisResult]) -> tuple:
        """Generate executive summary and limitations section."""
        
        completed = [ar for ar in analysis_results if ar.status == AnalysisStatus.COMPLETED]
        skipped = [ar for ar in analysis_results if ar.status == AnalysisStatus.SKIPPED]
        failed = [ar for ar in analysis_results if ar.status == AnalysisStatus.FAILED]
        
        all_warnings = []
        all_limitations = []
        confidence_scores = []
        
        for ar in completed:
            if ar.warnings:
                all_warnings.extend(ar.warnings)
            if ar.limitations:
                all_limitations.extend(ar.limitations)
            if ar.confidence_score:
                confidence_scores.append(ar.confidence_score)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        summary = (
            f"Analysis completed for {len(completed)} modules. "
            f"{len(skipped)} modules skipped due to quality or applicability constraints. "
            f"Average confidence score: {avg_confidence:.1f}%. "
            f"{len(all_warnings)} warnings identified requiring attention."
        )
        
        limitations = "\n".join(set(all_limitations)) if all_limitations else "No specific limitations noted."
        
        return summary, limitations
    
    @staticmethod
    async def get_report(db: AsyncSession, report_id: int, user: User) -> Report:
        """Get a report by ID with access control."""
        
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        
        case_result = await db.execute(select(Case).where(Case.id == report.case_id))
        case = case_result.scalar_one_or_none()
        
        if case.agency_id != user.agency_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        await create_audit_log(
            db=db,
            action=AuditAction.REPORT_VIEW,
            user_id=user.id,
            agency_id=user.agency_id,
            resource_type="report",
            resource_id=report.id,
            resource_uuid=report.uuid
        )
        
        return report
    
    @staticmethod
    async def list_reports_for_case(db: AsyncSession, case_id: int, user: User) -> List[Report]:
        """List all reports for a case."""
        
        case_result = await db.execute(select(Case).where(Case.id == case_id))
        case = case_result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
        if case.agency_id != user.agency_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        result = await db.execute(
            select(Report)
            .where(Report.case_id == case_id)
            .order_by(Report.created_at.desc())
        )
        
        return list(result.scalars().all())

"""PDF report generation service"""
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Service to generate PDF reports for water bodies monitoring"""
    
    @staticmethod
    def generate_15day_report(
        water_bodies_data: list,
        historical_data: dict,
        report_title: str = "15-Day Water Bodies Monitoring Report"
    ) -> BytesIO:
        """
        Generate a 15-day monitoring report as PDF
        
        Args:
            water_bodies_data: List of water body summaries
            historical_data: Dictionary of historical records for each water body
            report_title: Title of the report
            
        Returns:
            BytesIO: PDF file content
        """
        try:
            # Create PDF buffer
            pdf_buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#0284C7'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#0284C7'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_LEFT
            )
            
            # Add title
            elements.append(Paragraph(report_title, title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Add report metadata
            metadata_data = [
                ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Monitoring Period:", "Last 15 Days"],
                ["Total Water Bodies:", str(len(water_bodies_data))],
            ]
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f9ff')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
            ]))
            
            elements.append(metadata_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add summary statistics
            elements.append(Paragraph("Summary Statistics", heading_style))
            
            summary_stats = PDFReportGenerator._calculate_summary_stats(water_bodies_data)
            
            stats_data = [
                ["Metric", "Value"],
                ["Total Water Bodies Monitored", str(len(water_bodies_data))],
                ["Encroached Water Bodies", str(summary_stats['encroached_count'])],
                ["Average Water Coverage", f"{summary_stats['avg_water']:.2f}%"],
                ["Maximum Water Coverage", f"{summary_stats['max_water']:.2f}%"],
                ["Minimum Water Coverage", f"{summary_stats['min_water']:.2f}%"],
                ["Average Encroachment", f"{summary_stats['avg_encroachment']:.2f}%"],
            ]
            
            stats_table = Table(stats_data, colWidths=[3.5*inch, 2.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284C7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add detailed water bodies table
            elements.append(Paragraph("Water Bodies Monitoring Details", heading_style))
            
            bodies_data = [["Water Body", "Avg Water %", "Avg Area (km²)", "Encroachment %", "Status"]]
            
            for body in water_bodies_data:
                status = "🚨 ENCROACHED" if body.get("is_encroached") else "✓ Normal"
                bodies_data.append([
                    body.get("name", "N/A")[:20],
                    f"{body.get('avg_water_percentage', 0):.1f}%",
                    f"{body.get('avg_area_sq_km', 0):.2f}",
                    f"{body.get('avg_encroachment_percentage', 0):.1f}%",
                    status
                ])
            
            bodies_table = Table(bodies_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.4*inch])
            bodies_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284C7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(bodies_table)
            elements.append(PageBreak())
            
            # Add recommendations
            elements.append(Paragraph("Recommendations & Actions", heading_style))
            
            recommendations = [
                "1. Priority Focus: Monitor encroached water bodies (marked with 🚨) closely",
                "2. Field Verification: Conduct ground survey for detected encroachment areas",
                "3. Legal Action: File necessary complaints for illegal constructions",
                "4. Conservation: Implement water conservation measures where needed",
                "5. Community Engagement: Raise awareness about water body protection",
                "6. Regular Monitoring: Continue satellite monitoring at least weekly",
            ]
            
            for rec in recommendations:
                elements.append(Paragraph(rec, normal_style))
                elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Spacer(1, 0.2*inch))
            
            # Add footer
            footer_text = "This report is generated automatically by the Watery Water Bodies Monitoring System.<br/>For concerns or inquiries, contact the administration."
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                borderPadding=10
            )))
            
            # Build PDF
            doc.build(elements)
            
            # Reset buffer position
            pdf_buffer.seek(0)
            
            logger.info("15-day PDF report generated successfully")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_summary_stats(water_bodies_data: list) -> dict:
        """Calculate summary statistics from water bodies data"""
        if not water_bodies_data:
            return {
                "encroached_count": 0,
                "avg_water": 0,
                "max_water": 0,
                "min_water": 0,
                "avg_encroachment": 0
            }
        
        water_percentages = [b.get("avg_water_percentage", 0) for b in water_bodies_data]
        encroachment_percentages = [b.get("avg_encroachment_percentage", 0) for b in water_bodies_data]
        encroached_count = sum(1 for b in water_bodies_data if b.get("is_encroached", False))
        
        return {
            "encroached_count": encroached_count,
            "avg_water": sum(water_percentages) / len(water_percentages) if water_percentages else 0,
            "max_water": max(water_percentages) if water_percentages else 0,
            "min_water": min(water_percentages) if water_percentages else 0,
            "avg_encroachment": sum(encroachment_percentages) / len(encroachment_percentages) if encroachment_percentages else 0
        }

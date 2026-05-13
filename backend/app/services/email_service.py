"""Email service for sending notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    @staticmethod
    def send_encroachment_alert(
        recipient_email: str,
        water_body_name: str,
        encroachment_details: dict = None,
    ) -> bool:
        """
        Send encroachment alert email
        
        Args:
            recipient_email: Email address of the recipient
            water_body_name: Name of the water body
            encroachment_details: Additional details about encroachment
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if SMTP is configured
            if not settings.smtp_user or not settings.smtp_pass:
                logger.warning("SMTP not configured - logging email instead of sending")
                logger.info(f"📧 EMAIL WOULD BE SENT to {recipient_email}")
                logger.info(f"Subject: 🚨 URGENT: Water Body Encroachment Detected - {water_body_name}")
                logger.info(f"Body: Water body '{water_body_name}' has been marked as encroached")
                if encroachment_details:
                    logger.info(f"Details: {encroachment_details}")
                return True
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 URGENT: Water Body Encroachment Detected - {water_body_name}"
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
            msg["To"] = recipient_email
            
            # Create HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="background-color: #f0f4f8; padding: 20px; border-radius: 8px;">
                        <div style="background-color: white; padding: 20px; border-radius: 8px; border-left: 4px solid #DC2626;">
                            <h1 style="color: #DC2626; margin-top: 0;">⚠️ Water Body Encroachment Alert</h1>
                            
                            <p>An encroachment has been detected on the following water body:</p>
                            
                            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 4px; margin: 15px 0;">
                                <h3 style="color: #0284C7; margin-top: 0;">{water_body_name}</h3>
                                
                                {f'<p><strong>Encroachment Details:</strong></p>' if encroachment_details else ''}
                                {f'<ul style="margin: 10px 0; padding-left: 20px;">' if encroachment_details else ''}
                                {f'<li>Percentage: {encroachment_details.get("percentage", "N/A")}%</li>' if encroachment_details and encroachment_details.get("percentage") else ''}
                                {f'<li>Type: {encroachment_details.get("type", "Unknown")}</li>' if encroachment_details and encroachment_details.get("type") else ''}
                                {f'<li>Detection Date: {encroachment_details.get("detected_date", "N/A")}</li>' if encroachment_details and encroachment_details.get("detected_date") else ''}
                                {f'</ul>' if encroachment_details else ''}
                            </div>
                            
                            <p style="background-color: #FEE2E2; padding: 10px; border-radius: 4px; border-left: 3px solid #DC2626;">
                                <strong>Immediate Action Required:</strong> Please review this alert and take necessary corrective measures.
                            </p>
                            
                            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                                <p style="color: #666; font-size: 12px; margin-bottom: 5px;">
                                    This is an automated alert from the Erodai Water Bodies Monitoring System.
                                </p>
                                <p style="color: #666; font-size: 12px;">
                                    For more information, please visit the monitoring dashboard.
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Also create plain text version as fallback
            text_body = f"""
            WATER BODY ENCROACHMENT ALERT
            
            An encroachment has been detected on: {water_body_name}
            
            This is an automated alert from the Erodai Water Bodies Monitoring System.
            
            Immediate Action Required: Please review this alert and take necessary corrective measures.
            """
            
            # Attach both text and HTML versions
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Encroachment alert email sent to {recipient_email} for {water_body_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_bulk_encroachment_alert(
        recipient_emails: list,
        water_body_name: str,
        encroachment_details: dict = None,
    ) -> dict:
        """
        Send encroachment alert to multiple recipients
        
        Args:
            recipient_emails: List of email addresses
            water_body_name: Name of the water body
            encroachment_details: Additional details about encroachment
            
        Returns:
            dict: Statistics about sent/failed emails
        """
        stats = {
            "sent": 0,
            "failed": 0,
            "recipients": recipient_emails,
        }
        
        for email in recipient_emails:
            if EmailService.send_encroachment_alert(email, water_body_name, encroachment_details):
                stats["sent"] += 1
            else:
                stats["failed"] += 1
        
        return stats
    
    @staticmethod
    def send_encroachment_report(recipient_email: str, water_bodies_data: list) -> bool:
        """
        Send comprehensive encroachment alert report to a user
        
        Args:
            recipient_email: Email address of the recipient
            water_bodies_data: List of encroached water bodies with details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not settings.smtp_user or not settings.smtp_pass:
                logger.warning("SMTP not configured - logging report email instead of sending")
                logger.info(f"📧 ENCROACHMENT REPORT EMAIL WOULD BE SENT to {recipient_email}")
                logger.info(f"Report contains {len(water_bodies_data)} encroached water bodies")
                return True
            
            # Calculate summary stats
            total_bodies = len(water_bodies_data)
            total_area = sum(float(wb.get('area', 0)) for wb in water_bodies_data)
            avg_encroachment = sum(float(wb.get('encroachment_percent', 0)) for wb in water_bodies_data) / total_bodies if total_bodies > 0 else 0
            total_population = sum(int(wb.get('nearby_population', 0)) for wb in water_bodies_data)
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "⚠️ ENCROACHMENT ALERT REPORT - Watery Water Bodies Monitoring System"
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
            msg["To"] = recipient_email
            
            # Build HTML report
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .header {{ background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                        .header h1 {{ margin: 0; font-size: 24px; }}
                        .container {{ background: #f0f4f8; padding: 20px; max-width: 1000px; margin: 0 auto; }}
                        .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #0284C7; }}
                        .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin: 15px 0; }}
                        .summary-card {{ background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 15px; border-radius: 8px; text-align: center; border: 2px solid #ddd; }}
                        .summary-card .number {{ font-size: 28px; font-weight: bold; color: #DC2626; }}
                        .summary-card .label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                        th {{ background: #0284C7; color: white; padding: 12px; text-align: left; font-weight: bold; }}
                        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
                        tr:nth-child(even) {{ background: #f9fafb; }}
                        .severity-high {{ color: #D97706; font-weight: bold; }}
                        .severity-critical {{ color: #DC2626; font-weight: bold; }}
                        .detail-section {{ background: #EFF6FF; padding: 15px; margin: 15px 0; border-left: 4px solid #0284C7; border-radius: 4px; }}
                        .actions {{ background: #F0FDF4; padding: 15px; border-left: 4px solid #22C55E; margin: 15px 0; border-radius: 4px; }}
                        .actions li {{ margin: 8px 0; }}
                        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #ddd; margin-top: 30px; }}
                        .critical-box {{ background: #FEE2E2; padding: 15px; border-left: 3px solid #DC2626; margin: 15px 0; border-radius: 4px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>⚠️ ENCROACHMENT ALERT REPORT</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px;">Watery Water Bodies Monitoring System</p>
                        </div>
                        
                        <div class="section">
                            <p>Dear Monitoring Officer,</p>
                            <p>This is an urgent alert report regarding encroachment detected in monitored water bodies across Erode District.</p>
                            
                            <div class="critical-box">
                                <strong style="color: #DC2626; font-size: 16px;">🔴 CRITICAL ALERT</strong>
                                <p style="margin: 10px 0 0 0;">Multiple water bodies show significant encroachment. Immediate administrative action is required.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #0284C7; margin-top: 0;">📊 Summary Report</h2>
                            <div class="summary-grid">
                                <div class="summary-card">
                                    <div class="number">{total_bodies}</div>
                                    <div class="label">Encroached Bodies</div>
                                </div>
                                <div class="summary-card">
                                    <div class="number">{avg_encroachment:.1f}%</div>
                                    <div class="label">Avg Encroachment</div>
                                </div>
                                <div class="summary-card">
                                    <div class="number">{total_area:.1f}</div>
                                    <div class="label">Total Area (sq km)</div>
                                </div>
                                <div class="summary-card">
                                    <div class="number">{total_population//1000}K</div>
                                    <div class="label">Nearby Population</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #DC2626; margin-top: 0;">🚨 Detailed Encroachment Data</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Water Body Name</th>
                                        <th>Type</th>
                                        <th>Encroachment %</th>
                                        <th>Water Level %</th>
                                        <th>Area (sq km)</th>
                                        <th>Severity</th>
                                    </tr>
                                </thead>
                                <tbody>
            """
            
            # Add water body rows
            for idx, wb in enumerate(water_bodies_data, 1):
                encroach_pct = float(wb.get('encroachment_percent', 0))
                water_level_pct = float(wb.get('water_level_percent', 85))
                severity = wb.get('severity', 'HIGH')
                severity_icon = '🔴' if severity == 'CRITICAL' else '🟠'
                severity_class = f'severity-{severity.lower()}'
                
                html_body += f"""
                                    <tr>
                                        <td><strong>{idx}. {wb.get('name', 'Unknown')}</strong></td>
                                        <td>{wb.get('type', 'Unknown')}</td>
                                        <td>{encroach_pct:.1f}%</td>
                                        <td>{water_level_pct:.1f}%</td>
                                        <td>{float(wb.get('area', 0)):.2f}</td>
                                        <td><span class="{severity_class}">{severity_icon} {severity}</span></td>
                                    </tr>
                """
            
            html_body += """
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #0284C7; margin-top: 0;">📍 Detailed Analysis by Water Body</h2>
            """
            
            # Add detailed analysis for each water body
            for idx, wb in enumerate(water_bodies_data, 1):
                encroach_pct = float(wb.get('encroachment_percent', 0))
                water_level_pct = float(wb.get('water_level_percent', 85))
                severity = wb.get('severity', 'HIGH')
                severity_icon = '🟠' if severity == 'HIGH' else '🔴'
                
                html_body += f"""
                            <div class="detail-section">
                                <h3 style="margin-top: 0; color: #0284C7;">{idx}. {wb.get('name', 'Unknown')} ({wb.get('type', 'Unknown')})</h3>
                                <p><strong>Description:</strong> {wb.get('description', 'N/A')}</p>
                                <p><strong>Encroachment:</strong> {encroach_pct:.1f}%</p>
                                <p><strong>Water Level:</strong> {water_level_pct:.1f}%</p>
                                <p><strong>Area:</strong> {float(wb.get('area', 0)):.2f} sq km</p>
                                <p><strong>Severity:</strong> {severity_icon} {severity}</p>
                                <p><strong>Water Quality:</strong> {wb.get('water_quality', 'Fair')}</p>
                                <p><strong>Nearby Population:</strong> {wb.get('nearby_population', 'N/A')}</p>
                                <p><strong>NDVI Index:</strong> {wb.get('ndvi_index', 'N/A')}</p>
                                <p><strong>NDBI Index:</strong> {wb.get('ndbi_index', 'N/A')}</p>
                            </div>
                """
            
            html_body += f"""
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #0284C7; margin-top: 0;">📊 Access Dashboard</h2>
                            <p><a href="http://localhost:3000/dashboard" style="background: #0284C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Open Monitoring Dashboard</a></p>
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #22C55E; margin-top: 0;">🔔 Recommended Actions</h2>
                            <div class="actions">
                                <ul style="margin: 0; padding-left: 20px;">
                                    <li><strong>Immediate:</strong> Review satellite images on the dashboard for each encroached water body</li>
                                    <li><strong>Assessment:</strong> Contact local authorities and water management bodies</li>
                                    <li><strong>Field Verification:</strong> Deploy monitoring teams to assess ground situation</li>
                                    <li><strong>Documentation:</strong> Document encroachment with photos and GPS coordinates</li>
                                    <li><strong>Legal Action:</strong> Initiate appropriate legal proceedings for unauthorized activities</li>
                                    <li><strong>Follow-up:</strong> Track remediation efforts and update status regularly</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2 style="color: #0284C7; margin-top: 0;">❓ Important Notes</h2>
                            <ul style="line-height: 1.8;">
                                <li>All measurements are based on satellite imagery analysis with AI confidence levels</li>
                                <li>Encroachment percentages are calculated as area loss compared to baseline measurements</li>
                                <li>Water quality assessments are from the latest monitoring records</li>
                                <li>Population figures are estimates based on nearby settlement areas</li>
                                <li>NDVI (Vegetation Index) and NDBI (Water Index) are satellite-derived indices</li>
                            </ul>
                        </div>
                        
                        <div class="footer">
                            <strong>Watery - Real-time Water Bodies Monitoring System</strong><br>
                            Erode District, Tamil Nadu | Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST<br><br>
                            This is an automated alert. Do not reply to this email. Contact your administrator for support.
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Create plain text version
            text_body = f"""
            ⚠️ ENCROACHMENT ALERT REPORT
            Watery Water Bodies Monitoring System
            
            SUMMARY:
            - Total Encroached Bodies: {total_bodies}
            - Average Encroachment: {avg_encroachment:.1f}%
            - Total Area: {total_area:.1f} sq km
            - Nearby Population: {total_population}
            
            ENCROACHED WATER BODIES:
            """
            
            for idx, wb in enumerate(water_bodies_data, 1):
                text_body += f"\n{idx}. {wb.get('name', 'Unknown')} - {float(wb.get('encroachment_percent', 0)):.1f}% encroached"
            
            text_body += f"""
            
            Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST
            This is an automated alert from Watery Monitoring System.
            """
            
            # Attach both text and HTML versions
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Encroachment report email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send report email to {recipient_email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

def send_email_alert(subject, body, to_email):
    smtp_server = settings.smtp_host
    smtp_port = settings.smtp_port
    smtp_user = settings.smtp_user or 'user@example.com'
    smtp_password = settings.smtp_pass or 'password'
    from_email = settings.smtp_user or smtp_user

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())

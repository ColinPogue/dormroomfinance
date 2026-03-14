import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_notification(keyword, category, article_url, total_articles):
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["NOTIFICATION_EMAIL"]

    subject = f"DormRoomFinance — New Article Posted #{total_articles}"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">New Article Posted ✅</h2>
        <p style="color: #666; font-size: 14px;">{datetime.now().strftime('%A, %B %d, %Y')}</p>

        <div style="background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0;">
            <p style="margin: 0 0 8px 0;"><strong>Topic:</strong> {keyword}</p>
            <p style="margin: 0 0 8px 0;"><strong>Category:</strong> {category}</p>
            <p style="margin: 0;"><strong>URL:</strong> <a href="{article_url}">{article_url}</a></p>
        </div>

        <p><a href="{article_url}" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Article</a></p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            Total articles published: <strong>{total_articles}</strong><br>
            DormRoomFinance automation running smoothly 🚀
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())

    print(f"Notification sent to {recipient}")


def send_failure_notification(keyword, error_message):
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["NOTIFICATION_EMAIL"]

    subject = "DormRoomFinance — Pipeline FAILED"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #e74c3c;">Pipeline Failed ❌</h2>
        <p style="color: #666; font-size: 14px;">{datetime.now().strftime('%A, %B %d, %Y')}</p>

        <div style="background: #fdf0f0; border-left: 4px solid #e74c3c; padding: 15px; margin: 20px 0;">
            <p style="margin: 0 0 8px 0;"><strong>Keyword:</strong> {keyword}</p>
            <p style="margin: 0;"><strong>Error:</strong> {error_message}</p>
        </div>

        <p style="color: #999; font-size: 12px;">No article was published today. The keyword was not consumed.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())

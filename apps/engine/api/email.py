"""
Email Service for AuthorFlow Studios
Sends job completion/failure notifications using Brevo (Sendinblue) API

Environment variables:
- BREVO_API_KEY: Brevo API key for sending transactional emails
- EMAIL_FROM_ADDRESS: Sender email address (default: noreply@authorflowstudios.com)
- EMAIL_FROM_NAME: Sender display name (default: AuthorFlow Studios)
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@authorflowstudios.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AuthorFlow Studios")
APP_URL = os.getenv("APP_URL", "https://authorflowstudios.rohimayapublishing.com")


def is_email_configured() -> bool:
    """Check if email service is configured."""
    return bool(BREVO_API_KEY)


async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    Send an email using Brevo API.

    Args:
        to_email: Recipient email address
        to_name: Recipient display name
        subject: Email subject line
        html_content: HTML body of the email
        text_content: Plain text fallback (optional)

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not BREVO_API_KEY:
        logger.warning("Email not sent - BREVO_API_KEY not configured")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={
                    "sender": {
                        "name": EMAIL_FROM_NAME,
                        "email": EMAIL_FROM_ADDRESS,
                    },
                    "to": [{"email": to_email, "name": to_name}],
                    "subject": subject,
                    "htmlContent": html_content,
                    "textContent": text_content or "",
                },
                timeout=10.0,
            )

            if response.status_code in (200, 201):
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Email send failed: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


async def send_job_completed_email(
    to_email: str,
    to_name: str,
    job_title: str,
    job_id: str,
    duration_minutes: int,
) -> bool:
    """
    Send job completion notification email.

    Args:
        to_email: User's email address
        to_name: User's display name
        job_title: Title of the audiobook
        job_id: Job UUID for download link
        duration_minutes: Total audio duration in minutes
    """
    download_url = f"{APP_URL}/job/{job_id}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f0a1f;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #a855f7; font-size: 28px; margin: 0;">AuthorFlow Studios</h1>
            </div>

            <!-- Main Content -->
            <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 16px; padding: 40px; text-align: center;">
                <!-- Success Icon -->
                <div style="width: 80px; height: 80px; background: rgba(34, 197, 94, 0.2); border-radius: 50%; margin: 0 auto 24px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 40px;">✓</span>
                </div>

                <h2 style="color: #ffffff; font-size: 24px; margin: 0 0 16px;">Your Audiobook is Ready!</h2>

                <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                    Great news, {to_name}! Your audiobook <strong style="color: #a855f7;">"{job_title}"</strong> has been successfully generated.
                </p>

                <!-- Stats -->
                <div style="background: rgba(0, 0, 0, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 32px;">
                    <div style="color: rgba(255, 255, 255, 0.6); font-size: 14px;">Total Duration</div>
                    <div style="color: #ffffff; font-size: 28px; font-weight: bold;">{duration_minutes} minutes</div>
                </div>

                <!-- CTA Button -->
                <a href="{download_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                    Download Your Audiobook
                </a>
            </div>

            <!-- Footer -->
            <div style="text-align: center; margin-top: 40px; color: rgba(255, 255, 255, 0.4); font-size: 14px;">
                <p style="margin: 0 0 8px;">You received this email because you created an audiobook on AuthorFlow Studios.</p>
                <p style="margin: 0;">
                    <a href="{APP_URL}/dashboard" style="color: #a855f7; text-decoration: none;">Go to Dashboard</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Your Audiobook is Ready!

    Great news, {to_name}! Your audiobook "{job_title}" has been successfully generated.

    Total Duration: {duration_minutes} minutes

    Download your audiobook: {download_url}

    --
    AuthorFlow Studios
    """

    return await send_email(
        to_email=to_email,
        to_name=to_name,
        subject=f"Your audiobook '{job_title}' is ready!",
        html_content=html_content,
        text_content=text_content,
    )


async def send_job_failed_email(
    to_email: str,
    to_name: str,
    job_title: str,
    job_id: str,
    error_message: str,
) -> bool:
    """
    Send job failure notification email.

    Args:
        to_email: User's email address
        to_name: User's display name
        job_title: Title of the audiobook
        job_id: Job UUID
        error_message: Error description
    """
    retry_url = f"{APP_URL}/job/{job_id}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f0a1f;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #a855f7; font-size: 28px; margin: 0;">AuthorFlow Studios</h1>
            </div>

            <!-- Main Content -->
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 40px; text-align: center;">
                <!-- Error Icon -->
                <div style="width: 80px; height: 80px; background: rgba(239, 68, 68, 0.2); border-radius: 50%; margin: 0 auto 24px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 40px;">!</span>
                </div>

                <h2 style="color: #ffffff; font-size: 24px; margin: 0 0 16px;">Audiobook Generation Failed</h2>

                <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                    We're sorry, {to_name}. There was an issue generating your audiobook <strong style="color: #ef4444;">"{job_title}"</strong>.
                </p>

                <!-- Error Details -->
                <div style="background: rgba(0, 0, 0, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 32px; text-align: left;">
                    <div style="color: rgba(255, 255, 255, 0.6); font-size: 14px; margin-bottom: 8px;">Error Details</div>
                    <div style="color: #ef4444; font-size: 14px; font-family: monospace;">{error_message}</div>
                </div>

                <!-- CTA Button -->
                <a href="{retry_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                    View Details & Retry
                </a>

                <p style="color: rgba(255, 255, 255, 0.5); font-size: 14px; margin-top: 24px;">
                    Need help? Contact us at support@authorflowstudios.com
                </p>
            </div>

            <!-- Footer -->
            <div style="text-align: center; margin-top: 40px; color: rgba(255, 255, 255, 0.4); font-size: 14px;">
                <p style="margin: 0;">
                    <a href="{APP_URL}/dashboard" style="color: #a855f7; text-decoration: none;">Go to Dashboard</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Audiobook Generation Failed

    We're sorry, {to_name}. There was an issue generating your audiobook "{job_title}".

    Error: {error_message}

    View details and retry: {retry_url}

    Need help? Contact us at support@authorflowstudios.com

    --
    AuthorFlow Studios
    """

    return await send_email(
        to_email=to_email,
        to_name=to_name,
        subject=f"Issue with your audiobook '{job_title}'",
        html_content=html_content,
        text_content=text_content,
    )


async def send_trial_ending_email(
    to_email: str,
    to_name: str,
    days_remaining: int,
) -> bool:
    """
    Send trial ending notification email.

    Args:
        to_email: User's email address
        to_name: User's display name
        days_remaining: Days until trial expires
    """
    upgrade_url = f"{APP_URL}/billing"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f0a1f;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #a855f7; font-size: 28px; margin: 0;">AuthorFlow Studios</h1>
            </div>

            <!-- Main Content -->
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 40px; text-align: center;">
                <h2 style="color: #ffffff; font-size: 24px; margin: 0 0 16px;">Your Trial is Ending Soon</h2>

                <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                    Hi {to_name}, your free trial ends in <strong style="color: #f59e0b;">{days_remaining} days</strong>.
                </p>

                <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px; line-height: 1.6; margin: 0 0 32px;">
                    Upgrade now to continue creating professional audiobooks with unlimited access to all voices and features.
                </p>

                <!-- CTA Button -->
                <a href="{upgrade_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                    View Plans & Upgrade
                </a>
            </div>

            <!-- Footer -->
            <div style="text-align: center; margin-top: 40px; color: rgba(255, 255, 255, 0.4); font-size: 14px;">
                <p style="margin: 0;">
                    <a href="{APP_URL}/dashboard" style="color: #a855f7; text-decoration: none;">Go to Dashboard</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Your Trial is Ending Soon

    Hi {to_name}, your free trial ends in {days_remaining} days.

    Upgrade now to continue creating professional audiobooks with unlimited access to all voices and features.

    View plans: {upgrade_url}

    --
    AuthorFlow Studios
    """

    return await send_email(
        to_email=to_email,
        to_name=to_name,
        subject=f"Your AuthorFlow trial ends in {days_remaining} days",
        html_content=html_content,
        text_content=text_content,
    )

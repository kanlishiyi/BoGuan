"""
郵件發送工具
============

提供將 PDF 報告作為附件發送到指定郵箱的能力。

依賴配置項請在 ``.env`` 中設置（見 README 說明）::

    SMTP_HOST=smtp.example.com
    SMTP_PORT=587
    SMTP_USER=alert-bot@example.com
    SMTP_PASSWORD=your_password
    SMTP_FROM=BoGuan Alert Bot <alert-bot@example.com>
    SMTP_USE_TLS=true
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import settings


def send_pdf_email(
    to_email: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    filename: str = "report.pdf",
) -> None:
    """
    發送帶有 PDF 附件的郵件。

    Args:
        to_email: 收件人郵箱
        subject: 郵件主題
        body: 郵件正文（純文本 UTF-8）
        pdf_bytes: PDF 文件字節內容
        filename: 附件文件名
    """
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST 未配置，無法發送郵件")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(body or "BoGuan 告警分析平台自動發送的 PDF 報告。")

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT

    if settings.SMTP_USE_TLS:
        server: smtplib.SMTP = smtplib.SMTP(host, port)
        server.starttls()
    else:
        server = smtplib.SMTP(host, port)

    try:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass


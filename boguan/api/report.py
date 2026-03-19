"""
PDF 報告與郵件 API
==================

提供：
- 根據根因分析結論生成 PDF 報告並下載
- 將生成的 PDF 報告發送到指定郵箱
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from ..core.pdf import generate_report_pdf
from ..core.email import send_pdf_email
from .agents import find_agent
from .auth import require_auth


router = APIRouter(prefix="/api/agents", tags=["report"])


class ReportRequest(BaseModel):
    alert_id: str
    report_text: str


class ReportEmailRequest(ReportRequest):
    to_email: EmailStr
    subject: str | None = None
    body: str | None = None


@router.post("/{aid}/report/pdf")
async def generate_pdf_api(
    aid: str,
    body: ReportRequest,
    user: dict = Depends(require_auth),
):
    """
    根據分析結論生成 PDF 報告並直接返回作為下載。

    前端可以將「根因結論」或最終報告內容作為 ``report_text`` 傳入。
    """
    if not find_agent(aid):
        raise HTTPException(404, "Agent 不存在")

    pdf_bytes = generate_report_pdf(body.alert_id, body.report_text)
    filename = f"boguan_report_{body.alert_id}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/{aid}/report/email")
async def send_pdf_email_api(
    aid: str,
    body: ReportEmailRequest,
    user: dict = Depends(require_auth),
):
    """
    生成 PDF 報告並發送到指定郵箱。
    """
    if not find_agent(aid):
        raise HTTPException(404, "Agent 不存在")

    pdf_bytes = generate_report_pdf(body.alert_id, body.report_text)

    subject = body.subject or f"BoGuan 告警分析報告 - {body.alert_id}"
    text_body = body.body or (
        "您好，\n\n"
        "這封郵件由「博觀告警分析平台」自動發送，附件為本次告警的根因分析 PDF 報告。\n\n"
        "如需進一步分析，可登錄平台查看完整對話與調查過程。\n"
    )

    try:
        send_pdf_email(
            to_email=body.to_email,
            subject=subject,
            body=text_body,
            pdf_bytes=pdf_bytes,
            filename=f"boguan_report_{body.alert_id}.pdf",
        )
    except RuntimeError as e:
        # 例如未配置 SMTP_HOST 時，返回 400 並給出清晰中文提示
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}


"""Email template management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplatePreviewRequest, TemplateTestSendRequest,
)
from db.models import EmailTemplate
from core.template_engine import template_engine

router = APIRouter(prefix="/api/v1/templates", tags=["模板"])


@router.post("", response_model=TemplateResponse)
async def create_template(req: TemplateCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(EmailTemplate).where(EmailTemplate.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"模板名 '{req.name}' 已存在")

    # Auto-extract variables if not provided
    variables = req.variables
    if not variables:
        variables = template_engine.extract_variables(req.html_body)
        variables += template_engine.extract_variables(req.subject)
        variables = sorted(set(variables))

    tpl = EmailTemplate(
        name=req.name,
        subject=req.subject,
        html_body=req.html_body,
        text_body=req.text_body,
        variables=variables,
        category=req.category,
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.get("")
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailTemplate).order_by(EmailTemplate.id.desc())
    if category:
        q = q.where(EmailTemplate.category == category)
    result = await db.execute(q)
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    tpl = await db.get(EmailTemplate, template_id)
    if not tpl:
        raise HTTPException(404, "模板不存在")
    return tpl


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, req: TemplateUpdate, db: AsyncSession = Depends(get_db)):
    tpl = await db.get(EmailTemplate, template_id)
    if not tpl:
        raise HTTPException(404, "模板不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(tpl, field, value)

    # Re-extract variables if html_body changed
    if req.html_body is not None:
        tpl.variables = sorted(set(
            template_engine.extract_variables(tpl.html_body)
            + template_engine.extract_variables(tpl.subject)
        ))

    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.delete("/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    tpl = await db.get(EmailTemplate, template_id)
    if not tpl:
        raise HTTPException(404, "模板不存在")
    await db.delete(tpl)
    await db.commit()
    return {"ok": True}


@router.post("/{template_id}/preview")
async def preview_template(
    template_id: int,
    req: TemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """用示例数据渲染模板预览。"""
    tpl = await db.get(EmailTemplate, template_id)
    if not tpl:
        raise HTTPException(404, "模板不存在")

    subject = template_engine.render(tpl.subject, req.data)
    html = template_engine.render(tpl.html_body, req.data)

    return {
        "subject": subject,
        "html": html,
        "variables_used": tpl.variables,
    }


@router.post("/{template_id}/test-send")
async def test_send_template(
    template_id: int,
    req: TemplateTestSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """发送测试邮件。"""
    from api.config import settings
    from core.smtp_pool import smtp_pool

    tpl = await db.get(EmailTemplate, template_id)
    if not tpl:
        raise HTTPException(404, "模板不存在")

    sender = settings.DEFAULT_SENDER_EMAIL
    password = settings.DEFAULT_PASSWORD
    if not sender or not password:
        raise HTTPException(400, "未配置默认 SMTP 账户，请在 config.yaml 中设置")

    subject = template_engine.render(tpl.subject, req.data)
    html = template_engine.render(tpl.html_body, req.data)

    try:
        await smtp_pool.send(
            sender=sender,
            password=password,
            to=req.to_email,
            subject=f"[TEST] {subject}",
            html=html,
            text=tpl.text_body or "",
        )
        return {"status": "ok", "message": f"测试邮件已发送到 {req.to_email}"}
    except Exception as e:
        raise HTTPException(500, f"发送失败: {e}")

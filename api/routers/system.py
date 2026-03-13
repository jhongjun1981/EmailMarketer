"""System routes — health check, SMTP management, quick send."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import SmtpAccountCreate, SmtpAccountUpdate, SmtpTestRequest
from db.models import SmtpAccount
from core.smtp_pool import smtp_pool, get_smtp_config

router = APIRouter(prefix="/api/v1/system", tags=["系统"])


@router.get("/health")
async def health():
    return {"status": "ok", "service": "EmailMarketer"}


@router.post("/smtp/test")
async def test_smtp(req: SmtpTestRequest):
    """测试 SMTP 连接。"""
    result = await smtp_pool.test_connection(req.email, req.password)
    if result == "ok":
        return {"status": "ok", "message": "SMTP 连接成功"}
    else:
        raise HTTPException(400, f"SMTP 连接失败: {result}")


@router.get("/smtp/accounts")
async def list_smtp_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SmtpAccount).order_by(SmtpAccount.id))
    accounts = result.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "email": a.email,
            "smtp_host": a.smtp_host,
            "smtp_port": a.smtp_port,
            "use_ssl": a.use_ssl,
            "daily_limit": a.daily_limit,
            "sent_today": a.sent_today,
            "is_active": a.is_active,
        }
        for a in accounts
    ]


@router.post("/smtp/accounts")
async def add_smtp_account(req: SmtpAccountCreate, db: AsyncSession = Depends(get_db)):
    """添加 SMTP 账户。"""
    # Auto-detect SMTP config if not provided
    host = req.smtp_host
    port = req.smtp_port
    ssl = req.use_ssl
    if not host:
        host, auto_port, auto_ssl = get_smtp_config(req.email)
        port = port or auto_port
        ssl = ssl if ssl is not None else auto_ssl

    account = SmtpAccount(
        name=req.name,
        email=req.email,
        password=req.password,
        smtp_host=host,
        smtp_port=port or 465,
        use_ssl=ssl if ssl is not None else True,
        daily_limit=req.daily_limit,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return {
        "id": account.id,
        "name": account.name,
        "email": account.email,
        "smtp_host": account.smtp_host,
        "message": "SMTP 账户已添加",
    }


@router.put("/smtp/accounts/{account_id}")
async def update_smtp_account(account_id: int, req: SmtpAccountUpdate, db: AsyncSession = Depends(get_db)):
    """修改 SMTP 账户。"""
    result = await db.execute(select(SmtpAccount).where(SmtpAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "SMTP 账户不存在")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)
    return {
        "id": account.id,
        "name": account.name,
        "email": account.email,
        "smtp_host": account.smtp_host,
        "message": "SMTP 账户已更新",
    }


@router.delete("/smtp/accounts/{account_id}")
async def delete_smtp_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """删除 SMTP 账户。"""
    result = await db.execute(select(SmtpAccount).where(SmtpAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "SMTP 账户不存在")

    await db.delete(account)
    await db.commit()
    return {"ok": True, "message": "SMTP 账户已删除"}


@router.post("/quick-send")
async def quick_send(
    to_email: str = Form(...),
    subject: str = Form(...),
    content: str = Form(""),
    smtp_account_id: int = Form(...),
    attachments: list[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
):
    """快速发送邮件（支持附件）。"""
    # 查找 SMTP 账户
    result = await db.execute(
        select(SmtpAccount).where(SmtpAccount.id == smtp_account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "SMTP 账户不存在")
    if not account.is_active:
        raise HTTPException(400, "该 SMTP 账户已停用")

    # 处理附件
    file_list = None
    if attachments:
        file_list = []
        for f in attachments:
            if f.filename:
                file_bytes = await f.read()
                file_list.append((f.filename, file_bytes))

    # 邮件正文
    html_body = content if "<" in content else f"<p>{content}</p>"

    try:
        await smtp_pool.send(
            sender=account.email,
            password=account.password,
            to=to_email,
            subject=subject,
            html=html_body,
            text=content,
            sender_name=account.name,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            use_ssl=account.use_ssl,
            attachments=file_list,
        )
    except Exception as e:
        raise HTTPException(500, f"发送失败: {e}")

    return {"status": "ok", "message": f"邮件已发送到 {to_email}"}

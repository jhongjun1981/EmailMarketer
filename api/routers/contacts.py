"""Contact management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import (
    ContactCreate, ContactUpdate, ContactBatchImport, ContactResponse,
)
from db.models import Contact, ContactStatus, Segment, contact_segment

router = APIRouter(prefix="/api/v1/contacts", tags=["联系人"])


@router.post("", response_model=ContactResponse)
async def create_contact(req: ContactCreate, db: AsyncSession = Depends(get_db)):
    """创建单个联系人。"""
    existing = await db.execute(select(Contact).where(Contact.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"邮箱 {req.email} 已存在")

    contact = Contact(
        email=req.email,
        name=req.name,
        company=req.company,
        phone=req.phone,
        custom_fields=req.custom_fields,
        source=req.source,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.post("/batch")
async def batch_import(req: ContactBatchImport, db: AsyncSession = Depends(get_db)):
    """批量导入联系人。"""
    created = 0
    skipped = 0

    for c in req.contacts:
        existing = await db.execute(select(Contact).where(Contact.email == c.email))
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        contact = Contact(
            email=c.email,
            name=c.name,
            company=c.company,
            phone=c.phone,
            custom_fields=c.custom_fields,
            source=c.source or "import",
        )
        db.add(contact)
        created += 1

        # Add to segment if specified
        if req.segment_id:
            await db.flush()
            await db.execute(
                contact_segment.insert().values(
                    contact_id=contact.id,
                    segment_id=req.segment_id,
                )
            )

    await db.commit()

    # Update segment count
    if req.segment_id:
        count_result = await db.execute(
            select(func.count()).select_from(contact_segment).where(
                contact_segment.c.segment_id == req.segment_id
            )
        )
        seg = await db.get(Segment, req.segment_id)
        if seg:
            seg.contact_count = count_result.scalar() or 0
            await db.commit()

    return {"created": created, "skipped": skipped, "total": created + skipped}


@router.get("")
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    segment_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """列出联系人（分页）。"""
    q = select(Contact)

    if status:
        q = q.where(Contact.status == status)
    if segment_id:
        q = q.join(contact_segment).where(contact_segment.c.segment_id == segment_id)
    if search:
        q = q.where(
            Contact.email.contains(search) | Contact.name.contains(search)
        )

    q = q.order_by(Contact.id.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    contacts = result.scalars().all()

    # Total count
    count_q = select(func.count(Contact.id))
    if status:
        count_q = count_q.where(Contact.status == status)
    total = (await db.execute(count_q)).scalar() or 0

    return {
        "items": [ContactResponse.model_validate(c) for c in contacts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "联系人不存在")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, req: ContactUpdate, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "联系人不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "联系人不存在")
    await db.delete(contact)
    await db.commit()
    return {"ok": True}


@router.post("/{contact_id}/segments/{segment_id}")
async def add_to_segment(contact_id: int, segment_id: int, db: AsyncSession = Depends(get_db)):
    """将联系人加入分段。"""
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(404, "联系人不存在")
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")

    try:
        await db.execute(
            contact_segment.insert().values(contact_id=contact_id, segment_id=segment_id)
        )
        segment.contact_count = (segment.contact_count or 0) + 1
        await db.commit()
    except Exception:
        pass  # Already in segment

    return {"ok": True}


@router.delete("/{contact_id}/segments/{segment_id}")
async def remove_from_segment(contact_id: int, segment_id: int, db: AsyncSession = Depends(get_db)):
    """从分段移除联系人。"""
    await db.execute(
        contact_segment.delete().where(
            contact_segment.c.contact_id == contact_id,
            contact_segment.c.segment_id == segment_id,
        )
    )
    segment = await db.get(Segment, segment_id)
    if segment and segment.contact_count > 0:
        segment.contact_count -= 1
    await db.commit()
    return {"ok": True}

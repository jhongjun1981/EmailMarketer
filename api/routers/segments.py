"""Segment management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import SegmentCreate, SegmentUpdate, SegmentResponse, ContactResponse
from db.models import Segment, Contact, ContactStatus, contact_segment

router = APIRouter(prefix="/api/v1/segments", tags=["分段"])


@router.post("", response_model=SegmentResponse)
async def create_segment(req: SegmentCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Segment).where(Segment.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"分段名 '{req.name}' 已存在")

    segment = Segment(
        name=req.name,
        description=req.description,
        is_dynamic=req.is_dynamic,
        rules=req.rules,
    )
    db.add(segment)
    await db.commit()
    await db.refresh(segment)
    return segment


@router.get("")
async def list_segments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Segment).order_by(Segment.id.desc()))
    segments = result.scalars().all()
    return [SegmentResponse.model_validate(s) for s in segments]


@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(segment_id: int, db: AsyncSession = Depends(get_db)):
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")
    return segment


@router.put("/{segment_id}", response_model=SegmentResponse)
async def update_segment(segment_id: int, req: SegmentUpdate, db: AsyncSession = Depends(get_db)):
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(segment, field, value)

    await db.commit()
    await db.refresh(segment)
    return segment


@router.delete("/{segment_id}")
async def delete_segment(segment_id: int, db: AsyncSession = Depends(get_db)):
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")
    await db.delete(segment)
    await db.commit()
    return {"ok": True}


@router.post("/{segment_id}/refresh")
async def refresh_segment(segment_id: int, db: AsyncSession = Depends(get_db)):
    """刷新动态分段成员。"""
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")
    if not segment.is_dynamic or not segment.rules:
        return {"message": "非动态分段，无需刷新", "contact_count": segment.contact_count}

    # Build dynamic query from rules
    rules = segment.rules
    q = select(Contact).where(Contact.status == ContactStatus.ACTIVE)

    field = rules.get("field", "")
    op = rules.get("op", "eq")
    value = rules.get("value", "")

    if field and hasattr(Contact, field):
        col = getattr(Contact, field)
        if op == "eq":
            q = q.where(col == value)
        elif op == "ne":
            q = q.where(col != value)
        elif op == "contains":
            q = q.where(col.contains(str(value)))

    result = await db.execute(q)
    matching_contacts = result.scalars().all()

    # Clear existing and re-add
    await db.execute(
        contact_segment.delete().where(contact_segment.c.segment_id == segment_id)
    )
    for contact in matching_contacts:
        await db.execute(
            contact_segment.insert().values(contact_id=contact.id, segment_id=segment_id)
        )

    segment.contact_count = len(matching_contacts)
    await db.commit()

    return {"message": "刷新完成", "contact_count": len(matching_contacts)}


@router.get("/{segment_id}/contacts")
async def get_segment_contacts(
    segment_id: int,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "分段不存在")

    result = await db.execute(
        select(Contact)
        .join(contact_segment)
        .where(contact_segment.c.segment_id == segment_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    contacts = result.scalars().all()
    return [ContactResponse.model_validate(c) for c in contacts]

"""Workflow management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import WorkflowCreate, WorkflowResponse
from db.models import (
    Workflow, WorkflowStatus, WorkflowStep, WorkflowExecution,
    ActionType, TriggerType,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["工作流"])


@router.post("", response_model=WorkflowResponse)
async def create_workflow(req: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    wf = Workflow(
        name=req.name,
        description=req.description,
        trigger_type=req.trigger_type,
        trigger_config=req.trigger_config,
    )
    db.add(wf)
    await db.flush()

    for i, step_data in enumerate(req.steps):
        step = WorkflowStep(
            workflow_id=wf.id,
            order=i + 1,
            action_type=step_data.action_type,
            config=step_data.config,
        )
        db.add(step)

    await db.commit()
    await db.refresh(wf)

    # Load steps for response
    steps_result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id).order_by(WorkflowStep.order)
    )
    steps = steps_result.scalars().all()

    return WorkflowResponse(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        status=wf.status.value if hasattr(wf.status, 'value') else wf.status,
        trigger_type=wf.trigger_type.value if hasattr(wf.trigger_type, 'value') else wf.trigger_type,
        trigger_config=wf.trigger_config or {},
        steps=[
            {"order": s.order, "action_type": s.action_type.value if hasattr(s.action_type, 'value') else s.action_type, "config": s.config}
            for s in steps
        ],
        created_at=wf.created_at,
    )


@router.get("")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.id.desc()))
    workflows = result.scalars().all()
    return [
        {
            "id": wf.id,
            "name": wf.name,
            "status": wf.status.value if hasattr(wf.status, 'value') else wf.status,
            "trigger_type": wf.trigger_type.value if hasattr(wf.trigger_type, 'value') else wf.trigger_type,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
        }
        for wf in workflows
    ]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "工作流不存在")

    steps_result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id).order_by(WorkflowStep.order)
    )
    steps = steps_result.scalars().all()

    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "status": wf.status.value if hasattr(wf.status, 'value') else wf.status,
        "trigger_type": wf.trigger_type.value if hasattr(wf.trigger_type, 'value') else wf.trigger_type,
        "trigger_config": wf.trigger_config,
        "steps": [
            {"order": s.order, "action_type": s.action_type.value if hasattr(s.action_type, 'value') else s.action_type, "config": s.config}
            for s in steps
        ],
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
    }


@router.post("/{workflow_id}/activate")
async def activate_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "工作流不存在")
    wf.status = WorkflowStatus.ACTIVE
    await db.commit()
    return {"ok": True, "status": "active"}


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "工作流不存在")
    wf.status = WorkflowStatus.PAUSED
    await db.commit()
    return {"ok": True, "status": "paused"}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: int, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "工作流不存在")
    await db.delete(wf)
    await db.commit()
    return {"ok": True}


@router.get("/{workflow_id}/executions")
async def workflow_executions(
    workflow_id: int,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    executions = result.scalars().all()

    return [
        {
            "id": e.id,
            "contact_id": e.contact_id,
            "status": e.status,
            "current_step_id": e.current_step_id,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "log": e.log,
        }
        for e in executions
    ]

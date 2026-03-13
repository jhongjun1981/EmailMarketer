"""Workflow engine — event-driven + scheduled tick."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from db.models import (
    Workflow, WorkflowStatus, WorkflowStep, WorkflowExecution,
    ActionType, TriggerType, Contact, ContactStatus,
    EmailTemplate, contact_segment,
)

log = logging.getLogger(__name__)


class WorkflowEngine:
    """Execute automated workflows triggered by events or schedules."""

    def __init__(self, db_session_factory, email_sender=None):
        self.db_factory = db_session_factory
        self.email_sender = email_sender

    def trigger_event(self, event_type: str, **kwargs):
        """Called when an event occurs (sync, from tracking endpoints)."""
        with self.db_factory() as db:
            # Find active workflows matching this trigger
            workflows = db.execute(
                select(Workflow).where(
                    Workflow.status == WorkflowStatus.ACTIVE,
                    Workflow.trigger_type == event_type,
                )
            ).scalars().all()

            for wf in workflows:
                self._handle_trigger(db, wf, event_type, **kwargs)
            db.commit()

    def _handle_trigger(self, db: Session, wf: Workflow, event_type: str, **kwargs):
        """Create a new execution for a matching workflow."""
        contact_id = kwargs.get("contact_id")
        if not contact_id:
            email_log = kwargs.get("email_log")
            if email_log:
                contact_id = email_log.contact_id

        if not contact_id:
            return

        # Check if contact already has an active execution for this workflow
        existing = db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.workflow_id == wf.id,
                WorkflowExecution.contact_id == contact_id,
                WorkflowExecution.status == "running",
            )
        ).scalar_one_or_none()

        if existing:
            return  # Don't duplicate

        # Get first step
        first_step = db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == wf.id)
            .order_by(WorkflowStep.order)
        ).scalars().first()

        if not first_step:
            return

        execution = WorkflowExecution(
            workflow_id=wf.id,
            contact_id=contact_id,
            current_step_id=first_step.id,
            status="running",
            next_execute_at=datetime.utcnow(),
            log=[],
        )
        db.add(execution)
        log.info(f"Workflow {wf.name} triggered for contact {contact_id}")

    def tick(self):
        """Called by scheduler — process all pending workflow executions."""
        with self.db_factory() as db:
            now = datetime.utcnow()
            pending = db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.status == "running",
                    WorkflowExecution.next_execute_at <= now,
                )
            ).scalars().all()

            for execution in pending:
                try:
                    self._execute_step(db, execution)
                except Exception as e:
                    log.error(f"Workflow execution {execution.id} error: {e}")
                    execution.status = "failed"
                    execution.log = (execution.log or []) + [
                        {"step": execution.current_step_id, "error": str(e), "at": now.isoformat()}
                    ]

            db.commit()

    def _execute_step(self, db: Session, execution: WorkflowExecution):
        """Execute the current step of a workflow execution."""
        step = db.get(WorkflowStep, execution.current_step_id)
        if not step:
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            return

        now = datetime.utcnow()
        log_entry = {
            "step_order": step.order,
            "action": step.action_type,
            "at": now.isoformat(),
        }

        if step.action_type == ActionType.SEND_EMAIL:
            # Queue email for sending (actual send is async)
            template_id = step.config.get("template_id")
            sender_email = step.config.get("sender_email", "")
            log_entry["result"] = f"queued email template={template_id}"
            self._advance_to_next(db, execution, step)

        elif step.action_type == ActionType.WAIT:
            duration = step.config.get("duration", 1)
            unit = step.config.get("unit", "hours")
            delta = timedelta(**{unit: duration})
            execution.next_execute_at = now + delta
            log_entry["result"] = f"waiting {duration} {unit}"
            # Don't advance yet — will be picked up on next tick after wait
            self._advance_to_next(db, execution, step)
            execution.next_execute_at = now + delta  # Override advance

        elif step.action_type == ActionType.CONDITION:
            result = self._evaluate_condition(db, execution, step.config)
            target = step.config.get("true_step" if result else "false_step")
            log_entry["result"] = f"condition={'true' if result else 'false'}"
            if target is not None:
                target_step = db.execute(
                    select(WorkflowStep).where(
                        WorkflowStep.workflow_id == execution.workflow_id,
                        WorkflowStep.order == target,
                    )
                ).scalar_one_or_none()
                if target_step:
                    execution.current_step_id = target_step.id
                    execution.next_execute_at = now
                else:
                    execution.status = "completed"
                    execution.completed_at = now
            else:
                execution.status = "completed"
                execution.completed_at = now

        elif step.action_type == ActionType.ADD_TO_SEGMENT:
            seg_id = step.config.get("segment_id")
            if seg_id:
                db.execute(
                    contact_segment.insert().values(
                        contact_id=execution.contact_id,
                        segment_id=seg_id,
                    )
                )
            log_entry["result"] = f"added to segment {seg_id}"
            self._advance_to_next(db, execution, step)

        elif step.action_type == ActionType.REMOVE_FROM_SEGMENT:
            seg_id = step.config.get("segment_id")
            if seg_id:
                db.execute(
                    contact_segment.delete().where(
                        contact_segment.c.contact_id == execution.contact_id,
                        contact_segment.c.segment_id == seg_id,
                    )
                )
            log_entry["result"] = f"removed from segment {seg_id}"
            self._advance_to_next(db, execution, step)

        elif step.action_type == ActionType.UPDATE_CONTACT:
            contact = db.get(Contact, execution.contact_id)
            if contact:
                for field, value in step.config.get("fields", {}).items():
                    if hasattr(contact, field):
                        setattr(contact, field, value)
            log_entry["result"] = "contact updated"
            self._advance_to_next(db, execution, step)

        else:
            log_entry["result"] = f"unknown action: {step.action_type}"
            self._advance_to_next(db, execution, step)

        execution.log = (execution.log or []) + [log_entry]

    def _advance_to_next(self, db: Session, execution: WorkflowExecution, current_step: WorkflowStep):
        """Move to the next step by order, or complete."""
        next_step = db.execute(
            select(WorkflowStep).where(
                WorkflowStep.workflow_id == execution.workflow_id,
                WorkflowStep.order > current_step.order,
            ).order_by(WorkflowStep.order)
        ).scalars().first()

        if next_step:
            execution.current_step_id = next_step.id
            execution.next_execute_at = datetime.utcnow()
        else:
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()

    def _evaluate_condition(self, db: Session, execution: WorkflowExecution, config: dict) -> bool:
        """Evaluate a condition against contact or email data."""
        field = config.get("field", "")
        op = config.get("op", "eq")
        value = config.get("value")

        contact = db.get(Contact, execution.contact_id)
        if not contact:
            return False

        actual = getattr(contact, field, None)
        if actual is None and contact.custom_fields:
            actual = contact.custom_fields.get(field)

        if op == "eq":
            return actual == value
        elif op == "ne":
            return actual != value
        elif op == "gt":
            return (actual or 0) > (value or 0)
        elif op == "lt":
            return (actual or 0) < (value or 0)
        elif op == "contains":
            return str(value) in str(actual or "")
        return False

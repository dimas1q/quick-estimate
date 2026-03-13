from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from datetime import datetime, timezone

from app.core.database import get_db
from app.models.note import Note
from app.models.estimate import Estimate
from app.models.client import Client
from app.models.template import EstimateTemplate
from app.models.changelog import EstimateChangeLog
from app.models.client_changelog import ClientChangeLog
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.utils.auth import get_current_user
from app.utils.workspace import (
    WORKSPACE_PERMISSION_DATA_EDIT,
    WORKSPACE_PERMISSION_DATA_VIEW,
    WorkspaceContext,
    require_workspace_permission,
)

router = APIRouter(tags=["notes"], dependencies=[Depends(get_current_user)])


async def _get_entity(db: AsyncSession, model, entity_id: int, organization_id: int):
    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity or entity.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return entity


async def _ensure_note_in_workspace(
    db: AsyncSession,
    note: Note,
    organization_id: int,
) -> None:
    if note.estimate_id:
        estimate = await db.get(Estimate, note.estimate_id)
        if not estimate or estimate.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Примечание не найдено")
        return
    if note.client_id:
        client = await db.get(Client, note.client_id)
        if not client or client.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Примечание не найдено")
        return
    if note.template_id:
        template = await db.get(EstimateTemplate, note.template_id)
        if not template or template.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Примечание не найдено")
        return
    raise HTTPException(status_code=404, detail="Примечание не найдено")


@router.get("/estimates/{estimate_id}/", response_model=List[NoteOut])
async def list_estimate_notes(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    await _get_entity(db, Estimate, estimate_id, context.organization_id)
    res = await db.execute(
        select(Note)
        .options(selectinload(Note.user))
        .where(Note.estimate_id == estimate_id)
        .order_by(Note.created_at.desc())
    )
    notes = res.scalars().all()
    return [
        NoteOut(
            id=n.id,
            text=n.text,
            created_at=n.created_at,
            updated_at=n.updated_at,
            user_id=n.user_id,
            user_name=n.user.name if n.user else None,
        )
        for n in notes
    ]


@router.post("/estimates/{estimate_id}/", response_model=NoteOut, status_code=201)
async def create_estimate_note(
    estimate_id: int,
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    estimate = await _get_entity(db, Estimate, estimate_id, context.organization_id)
    if estimate.read_only:
        raise HTTPException(
            status_code=409,
            detail="Смета находится в режиме только чтение",
        )
    note = Note(text=note_in.text, estimate_id=estimate_id, user_id=user.id)
    db.add(note)

    now = datetime.now(timezone.utc)
    log_details = [{"label": "Примечание", "new": note_in.text}]
    db.add(
        EstimateChangeLog(
            estimate_id=estimate_id,
            user_id=user.id,
            action="Добавление примечания",
            description="Добавлено примечание",
            details=log_details,
            timestamp=now,
        )
    )
    if estimate.client_id:
        db.add(
            ClientChangeLog(
                client_id=estimate.client_id,
                user_id=user.id,
                action="Добавление примечания",
                description=f"Добавлено примечание в смете: {estimate.name}",
                details=log_details,
                timestamp=now,
            )
        )

    await db.commit()
    await db.refresh(note)
    return NoteOut(
        id=note.id,
        text=note.text,
        created_at=note.created_at,
        updated_at=note.updated_at,
        user_id=note.user_id,
        user_name=user.name,
    )


@router.get("/clients/{client_id}/", response_model=List[NoteOut])
async def list_client_notes(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    await _get_entity(db, Client, client_id, context.organization_id)
    res = await db.execute(
        select(Note)
        .options(selectinload(Note.user))
        .where(Note.client_id == client_id)
        .order_by(Note.created_at.desc())
    )
    notes = res.scalars().all()
    return [
        NoteOut(
            id=n.id,
            text=n.text,
            created_at=n.created_at,
            updated_at=n.updated_at,
            user_id=n.user_id,
            user_name=n.user.name if n.user else None,
        )
        for n in notes
    ]


@router.post("/clients/{client_id}/", response_model=NoteOut, status_code=201)
async def create_client_note(
    client_id: int,
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    await _get_entity(db, Client, client_id, context.organization_id)
    note = Note(text=note_in.text, client_id=client_id, user_id=user.id)
    db.add(note)

    now = datetime.now(timezone.utc)
    log_details = [{"label": "Примечание", "new": note_in.text}]
    db.add(
        ClientChangeLog(
            client_id=client_id,
            user_id=user.id,
            action="Добавление примечания",
            description="Добавлено примечание",
            details=log_details,
            timestamp=now,
        )
    )

    await db.commit()
    await db.refresh(note)
    return NoteOut(
        id=note.id,
        text=note.text,
        created_at=note.created_at,
        updated_at=note.updated_at,
        user_id=note.user_id,
        user_name=user.name,
    )


@router.get("/templates/{template_id}/", response_model=List[NoteOut])
async def list_template_notes(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    await _get_entity(db, EstimateTemplate, template_id, context.organization_id)
    res = await db.execute(
        select(Note)
        .options(selectinload(Note.user))
        .where(Note.template_id == template_id)
        .order_by(Note.created_at.desc())
    )
    notes = res.scalars().all()
    return [
        NoteOut(
            id=n.id,
            text=n.text,
            created_at=n.created_at,
            updated_at=n.updated_at,
            user_id=n.user_id,
            user_name=n.user.name if n.user else None,
        )
        for n in notes
    ]


@router.post("/templates/{template_id}/", response_model=NoteOut, status_code=201)
async def create_template_note(
    template_id: int,
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    await _get_entity(db, EstimateTemplate, template_id, context.organization_id)
    note = Note(text=note_in.text, template_id=template_id, user_id=user.id)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteOut(
        id=note.id,
        text=note.text,
        created_at=note.created_at,
        updated_at=note.updated_at,
        user_id=note.user_id,
        user_name=user.name,
    )


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(
        select(Note)
        .options(
            selectinload(Note.user),
            selectinload(Note.estimate),
            selectinload(Note.client),
        )
        .where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Примечание не найдено")
    await _ensure_note_in_workspace(db, note, context.organization_id)
    if note.estimate_id and note.estimate and note.estimate.read_only:
        raise HTTPException(
            status_code=409,
            detail="Смета находится в режиме только чтение",
        )

    old_text = note.text
    note.text = note_in.text

    now = datetime.now(timezone.utc)
    log_details = [{"label": "Примечание", "old": old_text, "new": note_in.text}]

    if note.estimate_id:
        db.add(
            EstimateChangeLog(
                estimate_id=note.estimate_id,
                user_id=user.id,
                action="Редактирование примечания",
                description="Примечание изменено",
                details=log_details,
                timestamp=now,
            )
        )
        if note.estimate and note.estimate.client_id:
            db.add(
                ClientChangeLog(
                    client_id=note.estimate.client_id,
                    user_id=user.id,
                    action="Редактирование примечания",
                    description=f"Изменено примечание в смете: {note.estimate.name}",
                    details=log_details,
                    timestamp=now,
                )
            )
    elif note.client_id:
        db.add(
            ClientChangeLog(
                client_id=note.client_id,
                user_id=user.id,
                action="Редактирование примечания",
                description="Примечание изменено",
                details=log_details,
                timestamp=now,
            )
        )

    await db.commit()
    await db.refresh(note)
    return NoteOut(
        id=note.id,
        text=note.text,
        created_at=note.created_at,
        updated_at=note.updated_at,
        user_id=note.user_id,
        user_name=note.user.name if note.user else None,
    )


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(
        select(Note)
        .options(selectinload(Note.estimate), selectinload(Note.client))
        .where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Примечание не найдено")
    await _ensure_note_in_workspace(db, note, context.organization_id)
    if note.estimate_id and note.estimate and note.estimate.read_only:
        raise HTTPException(
            status_code=409,
            detail="Смета находится в режиме только чтение",
        )

    old_text = note.text
    now = datetime.now(timezone.utc)
    log_details = [{"label": "Примечание", "old": old_text}]

    if note.estimate_id:
        db.add(
            EstimateChangeLog(
                estimate_id=note.estimate_id,
                user_id=user.id,
                action="Удаление примечания",
                description="Примечание удалено",
                details=log_details,
                timestamp=now,
            )
        )
        if note.estimate and note.estimate.client_id:
            db.add(
                ClientChangeLog(
                    client_id=note.estimate.client_id,
                    user_id=user.id,
                    action="Удаление примечания",
                    description=f"Удалено примечание в смете: {note.estimate.name}",
                    details=log_details,
                    timestamp=now,
                )
            )
    elif note.client_id:
        db.add(
            ClientChangeLog(
                client_id=note.client_id,
                user_id=user.id,
                action="Удаление примечания",
                description="Примечание удалено",
                details=log_details,
                timestamp=now,
            )
        )

    await db.delete(note)
    await db.commit()
    return None

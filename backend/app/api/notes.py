from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from datetime import datetime, timezone

from app.core.database import get_db
from app.models.note import Note
from app.models.estimate import Estimate
from app.models.client import Client
from app.models.template import EstimateTemplate
from app.models.user import User
from app.models.changelog import EstimateChangeLog
from app.models.client_changelog import ClientChangeLog
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.utils.auth import get_current_user

router = APIRouter(tags=["notes"], dependencies=[Depends(get_current_user)])


async def _get_entity(db: AsyncSession, model, entity_id: int, user_id: int):
    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity or entity.user_id != user_id:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return entity


@router.get("/estimates/{estimate_id}/", response_model=List[NoteOut])
async def list_estimate_notes(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_entity(db, Estimate, estimate_id, user.id)
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
    user: User = Depends(get_current_user),
):
    estimate = await _get_entity(db, Estimate, estimate_id, user.id)
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
    user: User = Depends(get_current_user),
):
    await _get_entity(db, Client, client_id, user.id)
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
    user: User = Depends(get_current_user),
):
    await _get_entity(db, Client, client_id, user.id)
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
    user: User = Depends(get_current_user),
):
    await _get_entity(db, EstimateTemplate, template_id, user.id)
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
    user: User = Depends(get_current_user),
):
    await _get_entity(db, EstimateTemplate, template_id, user.id)
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
    user: User = Depends(get_current_user),
):
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
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Note)
        .options(selectinload(Note.estimate), selectinload(Note.client))
        .where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Примечание не найдено")

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

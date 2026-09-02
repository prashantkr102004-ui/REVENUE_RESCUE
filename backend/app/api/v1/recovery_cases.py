import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery_case import RecoveryCaseRead

router = APIRouter(prefix="/recovery-cases", tags=["recovery-cases"])


@router.get("", response_model=list[RecoveryCaseRead])
def list_recovery_cases(db: Session = Depends(get_db)) -> list[RecoveryCase]:
    return list(db.scalars(select(RecoveryCase).order_by(RecoveryCase.created_at.desc())))


@router.get("/{recovery_case_id}", response_model=RecoveryCaseRead)
def get_recovery_case(recovery_case_id: uuid.UUID, db: Session = Depends(get_db)) -> RecoveryCase:
    recovery_case = db.get(RecoveryCase, recovery_case_id)
    if recovery_case is None:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    return recovery_case

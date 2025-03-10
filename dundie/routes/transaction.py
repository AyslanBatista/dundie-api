from asyncio import sleep
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, WebSocket
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy.orm import aliased
from sqlmodel import Session, select, text

from dundie.auth import AuthenticatedUser
from dundie.db import ActiveSession
from dundie.models import Transaction, User
from dundie.models.serializers import TransactionResponse
from dundie.tasks.transaction import TransactionError, add_transaction

router = APIRouter()


@router.post('/{username}/', status_code=201)
async def create_transaction(
    *,
    username: str,
    value: int = Body(embed=True),
    current_user: User = AuthenticatedUser,
    session: Session = ActiveSession,
):
    """Adds a new transaction to the specified user."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        add_transaction(
            user=user, from_user=current_user, value=value, session=session
        )
    except TransactionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # At this point there was no error, so we can return
    return {"message": "Transaction added"}


@router.get("/", response_model=Page[TransactionResponse])
async def list_transactions(
    *,
    current_user: User = AuthenticatedUser,
    session: Session = ActiveSession,
    params: Params = Depends(),
    user: Optional[str] = None,
    from_user: Optional[str] = None,
    order_by: Optional[str] = None,  # &order_by=date,value -date,-value
):
    """Lists all transactions - for websocket version apeend /ws at the end"""
    query = select(Transaction)

    # Optional filters
    if user:
        query = query.join(User, Transaction.user_id == User.id).where(
            User.username == user
        )

    if from_user:
        FromUser = aliased(User)
        query = query.join(FromUser, Transaction.from_id == FromUser.id).where(
            FromUser.username == from_user
        )

    # access filters
    if not current_user.superuser:
        query = query.where(
            (Transaction.user_id == current_user.id)
            | (Transaction.from_id == current_user.id)
        )

    if order_by:
        order_text = text(
            order_by.replace("-", "")
            + " "
            + ("desc" if "-" in order_by else ("asc"))
        )
        query = query.order_by(order_text)

    return paginate(query=query, session=session, params=params)


@router.websocket("/ws")
async def list_transactions_ws(
    websocket: WebSocket, session: Session = ActiveSession
):
    await websocket.accept()
    last = 0
    while True:
        # Read all transactions that have not been seen yet
        new_transactions = session.exec(
            select(Transaction).where(Transaction.id > last).order_by("id")
        )
        for transaction in new_transactions:
            data = {
                "to": transaction.user.name,
                "from": transaction.from_user.name,
                "value": transaction.value,
            }
            await websocket.send_json(data)

            # set the last sent ID to avoid duplication
            last = transaction.id

            # Sleep 1 second (just to see better on UI)
            await sleep(1)

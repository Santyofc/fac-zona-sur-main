"""
Clients Router — CRUD de clientes por empresa
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from database import get_db
from models.models import User, Client
from schemas.schemas import ClientCreate, ClientUpdate, ClientResponse
from routers.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar clientes de la empresa actual."""
    query = select(Client).where(
        Client.company_id == current_user.company_id,
        Client.is_active == True
    )
    if search:
        query = query.where(Client.name.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit).order_by(Client.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear un nuevo cliente."""
    client = Client(**data.model_dump(), company_id=current_user.company_id)
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener un cliente por ID."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.company_id == current_user.company_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar un cliente."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.company_id == current_user.company_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.flush()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar (desactivar) un cliente."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.company_id == current_user.company_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    client.is_active = False

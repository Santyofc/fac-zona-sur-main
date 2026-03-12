"""
Products Router — CRUD de productos por empresa
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from database import get_db
from models.models import User, Product
from schemas.schemas import ProductCreate, ProductUpdate, ProductResponse
from routers.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar productos/servicios de la empresa."""
    query = select(Product).where(
        Product.company_id == current_user.company_id,
        Product.is_active == True
    )
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit).order_by(Product.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear un nuevo producto/servicio."""
    product = Product(**data.model_dump(), company_id=current_user.company_id)
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.company_id == current_user.company_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.company_id == current_user.company_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.flush()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.company_id == current_user.company_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    product.is_active = False

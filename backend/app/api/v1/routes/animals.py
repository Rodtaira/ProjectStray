from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/animals", tags=["animals"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("", dependencies=[Depends(get_current_user)])
async def create_animal():
    _not_implemented()


@router.get("/{animal_id}", dependencies=[Depends(get_current_user)])
async def get_animal(animal_id: str):
    _not_implemented()


@router.patch("/{animal_id}", dependencies=[Depends(get_current_user)])
async def update_animal(animal_id: str):
    """TODO: autorização adicional — só o dono do registro OU um
    moderador pode atualizar, não basta estar autenticado."""
    _not_implemented()


@router.get("", dependencies=[Depends(get_current_user)])
async def list_animals():
    _not_implemented()

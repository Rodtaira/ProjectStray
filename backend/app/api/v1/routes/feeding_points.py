from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/feeding-points", tags=["feeding-points"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("", dependencies=[Depends(get_current_user)])
async def create_feeding_point():
    _not_implemented()


@router.get("", dependencies=[Depends(get_current_user)])
async def list_feeding_points():
    """LEMBRETE: arredondar coordenadas na resposta, mesmo autenticado —
    não devolver o ponto exato do banco pra fora do backend."""
    _not_implemented()


@router.patch("/{feeding_point_id}", dependencies=[Depends(get_current_user)])
async def update_feeding_point(feeding_point_id: str):
    _not_implemented()

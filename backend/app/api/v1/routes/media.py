from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/media", tags=["media"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.post("/upload-url", dependencies=[Depends(get_current_user)])
async def get_upload_url():
    """Validar tipo e tamanho do arquivo ANTES de gerar a URL assinada do
    S3/MinIO — senão o bucket vira hospedagem de arquivo arbitrário."""
    _not_implemented()


@router.post("/{media_id}/confirm", dependencies=[Depends(get_current_user)])
async def confirm_upload(media_id: str):
    """Dispara o worker em background que remove EXIF e gera o embedding —
    nunca fazer isso de forma síncrona dentro do request."""
    _not_implemented()

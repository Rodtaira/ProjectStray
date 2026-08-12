from fastapi import APIRouter, Depends, HTTPException, WebSocket, status

from app.api.deps import get_current_user

router = APIRouter(prefix="/conversations", tags=["chat"])


def _not_implemented():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")


@router.get("", dependencies=[Depends(get_current_user)])
async def list_conversations():
    _not_implemented()


@router.post("", dependencies=[Depends(get_current_user)])
async def create_conversation():
    """Lembrar do rate limit de criação de DM — vetor de abuso/assédio
    já discutido na arquitetura de moderação."""
    _not_implemented()


@router.get("/{conversation_id}/messages", dependencies=[Depends(get_current_user)])
async def list_messages(conversation_id: str):
    """TODO: checar que o usuário autenticado é participante dessa
    conversa — não basta estar logado em qualquer conta."""
    _not_implemented()


@router.post("/{conversation_id}/read", dependencies=[Depends(get_current_user)])
async def mark_as_read(conversation_id: str):
    _not_implemented()


ws_router = APIRouter(tags=["chat"])


@ws_router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """TODO: validar o token no handshake antes de aceitar a conexão —
    ver a arquitetura de Redis pub/sub multi-instância já desenhada."""
    await websocket.close(code=1011)  # ainda não implementado

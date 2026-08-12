from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/payments/{provider}")
async def payment_webhook(provider: str, request: Request):
    """ATENÇÃO (SEGURANÇA): essa rota NUNCA usa JWT — quem chama é o gateway
    de pagamento, não um usuário logado. A autenticidade vem da validação da
    assinatura criptográfica do provedor (cada gateway tem seu mecanismo,
    ex: header X-Signature). Sem essa validação, qualquer um pode forjar uma
    confirmação de doação falsa no ledger. Validar a assinatura ANTES de
    processar o payload, e responder 401 se não bater — essa é provavelmente
    a rota mais sensível de toda a API.
    """
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Endpoint ainda não implementado")

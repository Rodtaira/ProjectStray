import mercadopago

from app.core.config import settings

_sdk = mercadopago.SDK(settings.mp_access_token)


def create_preference(
    *,
    title: str,
    amount: float,
    external_reference: str,
    success_url: str,
) -> dict:
    """Cria uma preferência de pagamento (Checkout Pro) e retorna a resposta
    da API — inclui 'id' (id da preferência) e 'init_point' (URL de checkout).

    external_reference é o id da NOSSA doação, não da campanha — é assim
    que o webhook consegue casar o pagamento de volta com o registro certo
    sem depender de nenhum campo específico do objeto de pagamento do MP.

    NÃO mandamos notification_url aqui de propósito: segundo a documentação
    do Mercado Pago, uma notification_url definida na criação do pagamento
    tem prioridade sobre a configurada no painel ("Suas integrações" →
    Webhooks) — só que a versão do painel é a única assinada com
    x-signature. Se mandássemos aqui, a notificação nunca teria assinatura
    validável, não importa a chave usada.
    """
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": "BRL",
            }
        ],
        "external_reference": external_reference,
        "back_urls": {
            "success": success_url,
            "failure": success_url,
            "pending": success_url,
        },
        "auto_return": "approved",
    }
    result = _sdk.preference().create(preference_data)
    response = result["response"]

    if "id" not in response:
        raise RuntimeError(f"Mercado Pago recusou a criação da preferência: {response}")

    return response


def get_payment(payment_id: str) -> dict:
    result = _sdk.payment().get(payment_id)
    return result["response"]
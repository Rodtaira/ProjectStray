# Stray — Documentação Técnica

App social de mapeamento e assistência a animais de rua e perdidos, com cadastro individual de animais, campanhas de crowdfunding para castração (priorizando fêmeas) e comunicação entre a comunidade.

Esta documentação reflete o estado real do código nesta etapa do projeto — não é um planejamento futuro, é o que está implementado e testado.

---

## 1. Arquitetura geral

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.12), assíncrono |
| Banco relacional/geoespacial | PostgreSQL 16 + PostGIS + pgvector |
| Cache, fila e rate limit | Redis 7 |
| Armazenamento de mídia | MinIO (S3-compatible) — provisionado, ainda sem endpoint de upload implementado |
| Pagamentos | Mercado Pago (Checkout Pro) |
| Frontend | React Native (Expo), TypeScript |
| Orquestração local | Docker Compose |
| Migrations | Alembic |

### Por que essas escolhas

- **PostGIS**: buscas por raio e clusterização geoespacial são o núcleo do produto (mapa de relatos de animais).
- **pgvector**: reservado para o matching de fotos "perdido × achado" via embeddings — schema pronto, worker de geração de embedding ainda não construído.
- **Redis**: cache, rate limiting (login/registro) e, futuramente, pub/sub para chat em tempo real.
- **Mercado Pago**: dos gateways brasileiros avaliados, é o único com suporte a Pix totalmente self-service para negócios domiciliados no Brasil (a Stripe exige convite para Pix nesse cenário).

---

## 2. Ambiente local

### 2.1 Serviços (`docker-compose.yml`)

| Serviço | Imagem/Build | Porta | Observação |
|---|---|---|---|
| `db` | build customizado (`pgvector/pgvector:pg16` + PostGIS via apt) | 5432 | ver `docker/postgres/Dockerfile` |
| `redis` | `redis:7-alpine` | 6379 | |
| `minio` | `minio/minio:latest` | 9000 (API) / 9001 (console) | bucket ainda criado manualmente |
| `backend` | build customizado (`python:3.12-slim`) | 8000 | roda como usuário não-root (ver §2.3) |

Todos os serviços têm `restart: unless-stopped`.

### 2.2 Variáveis de ambiente (`backend/.env`)

```
DATABASE_URL=postgresql+asyncpg://appuser:apppassword@db:5432/app_db
REDIS_URL=redis://redis:6379/0

S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=animal-media

JWT_SECRET_KEY=<gerado com secrets.token_hex(32)>
JWT_ALGORITHM=HS256

MP_ACCESS_TOKEN=<access token de TESTE do Mercado Pago>
MP_WEBHOOK_SECRET=<assinatura secreta do webhook, modo TESTE>
PUBLIC_BACKEND_URL=<URL pública do túnel — ngrok/cloudflared em dev>

ENVIRONMENT=development
```

**Nunca committar o `.env` real** — só o `.env.example` com placeholders vai pro controle de versão.

### 2.3 Container do backend roda como usuário não-root

O `Dockerfile` do backend recebe `HOST_UID`/`HOST_GID` como build args (via `docker-compose.yml`, lidos do ambiente do shell) e cria um usuário `appuser` com esse UID/GID, evitando que arquivos gerados pelo container (migrations, bytecode) apareçam como propriedade de `root` no host.

```bash
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)
docker compose up -d --build
```

### 2.4 Alembic — três gotchas resolvidos que valem documentar

1. **PostGIS cria `spatial_ref_sys`, uma tabela que não pertence a nenhum modelo nosso.** Sem tratamento, o autogenerate do Alembic tenta apagá-la a cada migration. Fix: `env.py` tem um filtro `include_object` que ignora tabelas de extensão.
2. **`Enum` do Postgres não é criado automaticamente em `ALTER TABLE ADD COLUMN`** (só em `CREATE TABLE`). Migrations que adicionam uma coluna `Enum` numa tabela existente precisam criar o tipo explicitamente com `postgresql.ENUM(..., create_type=False)` + `.create(op.get_bind(), checkfirst=True)` antes do `add_column`.
3. **GeoAlchemy2 cria índice espacial automaticamente**, a menos que a coluna declare `spatial_index=False`. Nesse caso, o índice precisa ser declarado explicitamente no modelo via `__table_args__ = (Index(...),)` — sem isso, o SQLAlchemy "esquece" que o índice existe e o autogenerate propõe apagá-lo a cada nova migration.
4. **Colunas novas `NOT NULL` em tabelas com dados existentes** usam `server_default` (não só `default` do Python) — isso deixa o próprio Postgres preencher as linhas antigas durante o `ALTER TABLE`, sem precisar apagar dado de teste.

---

## 3. Modelo de dados

### 3.1 `users`

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID (PK) | |
| `email` | string, único, indexado | |
| `phone` | string, opcional | |
| `full_name` | string, opcional | |
| `password_hash` | string | bcrypt |
| `role` | enum `common` \| `moderator` \| `admin` | default `common` |
| `created_at` | timestamp | |
| `deleted_at` | timestamp, opcional | reservado para rotina de anonimização (ainda não implementada) |

### 3.2 `sightings` (relatos de avistamento)

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID (PK) | |
| `reporter_id` | UUID (FK `users`) | obrigatório, indexado |
| `description` | string, opcional | |
| `status` | enum `open` \| `resolved` | default `open` |
| `location` | `Geography(POINT, 4326)` | índice GIST declarado explicitamente (ver §2.4.3) |
| `photo_embedding` | `vector(512)`, opcional | reservado para matching por IA — não populado ainda |
| `created_at` | timestamp | |

### 3.3 `animals`

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID (PK) | |
| `registered_by` | UUID (FK `users`) | obrigatório, indexado |
| `species` | enum `dog` \| `cat` | imutável após criação |
| `sex` | enum `male` \| `female` \| `unknown` | default `unknown` |
| `name` | string, opcional | |
| `description` | string, opcional | |
| `is_sterilized` | boolean | default `false` — só muda via `PATCH`, nunca no cadastro |
| `status` | enum `stray` \| `adopted` \| `in_shelter` \| `deceased` | default `stray` |
| `created_at` | timestamp | |

### 3.4 `campaigns`

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID (PK) | |
| `created_by` | UUID (FK `users`) | obrigatório, indexado |
| `animal_id` | UUID (FK `animals`), opcional | campanha pode ser regional/geral |
| `title` | string | |
| `description` | string, opcional | |
| `goal_amount` | `Numeric(10,2)` | nunca float — dinheiro não usa ponto flutuante |
| `status` | enum `active` \| `funded` \| `completed` \| `cancelled` | default `active` |
| `created_at` | timestamp | |

### 3.5 `donations`

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID (PK) | usado como `external_reference` no Mercado Pago |
| `campaign_id` | UUID (FK `campaigns`) | obrigatório, indexado |
| `donor_id` | UUID (FK `users`), opcional | |
| `amount` | `Numeric(10,2)` | |
| `payment_reference` | string, único | id da preferência de pagamento no Mercado Pago (auditoria) |
| `status` | enum `pending` \| `confirmed` \| `refunded` | default `pending`, só o webhook confirma |
| `created_at` | timestamp | |

### 3.6 Relacionamentos

```
users 1───N sightings (reporter_id)
users 1───N animals (registered_by)
users 1───N campaigns (created_by)
users 1───N donations (donor_id, opcional)
animals 1───N campaigns (animal_id, opcional)
campaigns 1───N donations (campaign_id)
```

---

## 4. Autenticação e autorização

### 4.1 Fluxo

- **Senha**: hash com `bcrypt` (não `passlib` — versão recente do `bcrypt` tem incompatibilidade documentada com `passlib`).
- **Tokens**: JWT assinado com `HS256`. Access token expira em 30 minutos, refresh token em 30 dias. Payload inclui `sub` (id do usuário) e `type` (`access` ou `refresh`), evitando que um refresh token seja aceito como access token por engano.
- **`POST /auth/register`** e **`POST /auth/login`** retornam ambos os tokens (registro já loga automaticamente).
- **`POST /auth/refresh`** troca um refresh token válido por um par novo.
- Mensagem de erro de login é genérica ("E-mail ou senha incorretos") propositalmente — não revela se o e-mail existe.

### 4.2 Autorização por papel

- `get_current_user`: valida o access token, carrega o usuário do banco.
- `get_current_moderator`: reaproveita `get_current_user`, exige `role` em (`moderator`, `admin`).
- Padrão de autorização usado em `sightings`, `animals` e `campaigns`: **dono do registro OU moderador** pode editar/remover. Qualquer usuário autenticado pode criar.

### 4.3 Rate limiting

Implementado com Redis (contador de janela fixa, `INCR` + `EXPIRE`), reutilizável via `RateLimiter(action, max_attempts, window_seconds)`:

- `POST /auth/register`: 5 tentativas/hora por IP
- `POST /auth/login`: 10 tentativas/15min por IP

### 4.4 Rotina de renovação automática (frontend)

O cliente HTTP do app (`lib/auth-client.ts`) intercepta `401`, tenta renovar via refresh token automaticamente e repete a chamada original **uma vez**. Chamadas concorrentes que tomam `401` ao mesmo tempo compartilham a mesma promise de renovação (evita gerar múltiplos refresh tokens em paralelo, que se invalidariam entre si).

---

## 5. Referência de API

Prefixo: `/api/v1`. `Pública` = sem autenticação necessária.

### Auth

| Método | Rota | Auth |
|---|---|---|
| POST | `/auth/register` | Pública (rate limited) |
| POST | `/auth/login` | Pública (rate limited) |
| POST | `/auth/refresh` | Pública |

### Users

| Método | Rota | Auth |
|---|---|---|
| GET | `/users/me` | JWT |
| PATCH | `/users/me` | JWT — **stub (501)** |
| DELETE | `/users/me` | JWT — **stub (501)**, aciona anonimização quando implementado |
| GET | `/users/{id}` | JWT — retorna `UserPublic`, nunca email/telefone |

### Sightings

| Método | Rota | Auth |
|---|---|---|
| POST | `/sightings` | JWT |
| GET | `/sightings` | JWT |
| GET | `/sightings/{id}` | JWT |
| PATCH | `/sightings/{id}` | JWT — dono ou moderador |
| GET | `/sightings/{id}/matches` | JWT — **stub (501)**, depende do worker de embedding |

Resposta arredonda `latitude`/`longitude` para 3 casas decimais (~100-110m) — a coordenada exata fica só no banco (ver §6.4).

### Animals

| Método | Rota | Auth |
|---|---|---|
| POST | `/animals` | JWT |
| GET | `/animals` | JWT — filtros opcionais `?species=` e `?status=` |
| GET | `/animals/{id}` | JWT |
| PATCH | `/animals/{id}` | JWT — dono ou moderador |
| DELETE | `/animals/{id}` | JWT — dono ou moderador; exclusão real, só para corrigir cadastro errado (mudança de ciclo de vida usa `status`, não delete) |

### Campaigns

| Método | Rota | Auth |
|---|---|---|
| POST | `/campaigns` | JWT — valida que `animal_id` existe, se informado |
| GET | `/campaigns` | **Pública** |
| GET | `/campaigns/{id}` | **Pública** |
| PATCH | `/campaigns/{id}` | JWT — dono ou moderador |
| POST | `/campaigns/{id}/donations` | JWT — cria preferência no Mercado Pago, retorna `checkout_url` |
| GET | `/campaigns/{id}/donations` | **Pública** — só doações `confirmed` |

### Webhooks

| Método | Rota | Auth |
|---|---|---|
| POST | `/webhooks/payments/mercadopago` | Assinatura HMAC (nunca JWT) |

### Ainda stub (só declaradas, retornam 501)

`auth` já implementado; os seguintes grupos existem como rota mas sem lógica: `feeding-points`, `moderation` (`/flags`, `/moderation/queue`, `/moderation/actions`), `chat` (`/conversations`, `/ws/chat`), `media` (`/media/upload-url`, `/media/{id}/confirm`), `matches` (`/matches/{id}/confirm`, `/matches/{id}/reject`).

---

## 6. Segurança — decisões e proteções implementadas

1. **JWT_SECRET_KEY** gerada com `secrets.token_hex(32)`, nunca hardcoded nem versionada.
2. **Rate limiting** em login/registro (§4.3).
3. **`UserPublic` nunca inclui email/telefone** — schema de resposta separado de `UserMe`.
4. **Container do backend roda como usuário não-root** (§2.3).
5. **Webhook do Mercado Pago valida assinatura HMAC-SHA256** antes de processar qualquer notificação — rejeita com `401` se não bater. Ver §7.4 para o algoritmo exato.
6. **Exclusão de conta (`DELETE /users/me`, ainda stub) está desenhada para nunca deletar em cascata** `sightings`/`donations`/mensagens — só sobrescrever dado pessoal, preservando histórico e ledger de doações.
7. **Coordenadas de `sightings` arredondadas na resposta pública** (§6.4) — a localização exata de quem reportou nunca é exposta pela API, mesmo autenticado.
8. **Nunca armazenamos dado de cartão** — o Checkout Pro do Mercado Pago é hospedado, o backend só lida com `preference_id`/`payment_id`.

### 6.4 Arredondamento de coordenada (privacidade)

`PUBLIC_COORDINATE_PRECISION = 3` em `app/services/sightings.py`. Isso equivale a uma margem de ~100-110m — suficiente para o mapa continuar útil ("tem animal por perto") sem expor onde exatamente alguém estava ao reportar (o que poderia indiretamente revelar onde mora).

---

## 7. Integração de pagamento (Mercado Pago)

### 7.1 Fluxo

1. `POST /campaigns/{id}/donations` cria um registro `Donation` (`status=pending`) e, em seguida, uma **preferência de pagamento** via SDK do Mercado Pago (Checkout Pro).
2. `external_reference` da preferência = **id da própria doação** (não o id da campanha) — é assim que a confirmação (por qualquer um dos dois caminhos abaixo) casa o pagamento de volta com o registro certo.
3. A resposta da API devolve `checkout_url` (`init_point`), pra onde o cliente redireciona o usuário.
4. Depois do pagamento, o Mercado Pago redireciona o navegador de volta pro `back_url` (mesma URL pra sucesso/falha/pendente: `GET /donations/callback`), incluindo `payment_id`, `external_reference` e `status` como query params.
5. `GET /donations/callback` **é o caminho principal de confirmação hoje**: reverifica o pagamento chamando a API autenticada do Mercado Pago com o `payment_id` recebido (nunca confia nos query params sozinhos) e, se `status == "approved"`, marca a doação como `confirmed`.
6. O webhook (`POST /webhooks/payments/mercadopago`) continua existindo e validando assinatura normalmente, mas é tratado como **reforço**, não como fonte primária — ver §7.4 para o motivo.
7. `GET /campaigns/{id}/donations` (ledger público) só lista doações `confirmed`.

### 7.2 SDK síncrono dentro de rota assíncrona

O SDK oficial do Mercado Pago (`mercadopago` no PyPI) é bloqueante. Chamado direto dentro de uma rota `async def`, travaria o event loop inteiro enquanto espera resposta da API externa. Solução: `starlette.concurrency.run_in_threadpool` isola a chamada numa thread, e `asyncio.wait_for(..., timeout=15)` garante que a requisição falha rápido (com erro claro) em vez de travar indefinidamente se a chamada nunca retornar.

### 7.3 Ambiente de teste vs. produção

O Mercado Pago separa **Access Token**, **URL de webhook** e **assinatura secreta** em duas versões completamente independentes: teste e produção. Os três precisam estar consistentemente do lado de teste durante desenvolvimento:

- Credenciais de teste: painel → aplicação → **Credenciais de teste** (confira sempre pela aba correta da página, o prefixo do token sozinho não é confiável pra diferenciar).
- Webhook: painel → aplicação → **Webhooks**, com abas separadas **Modo de teste** / **Modo de produção** — cada uma com sua própria URL e assinatura secreta.
- Pagamento de teste exige uma **conta compradora de teste** (criada em "Contas de teste"), logada durante o checkout — pagar como comprador "real" contra uma preferência de teste gera o erro `"Uma das partes... é de teste"`.

### 7.4 Por que o webhook não é a confirmação primária hoje

Duas descobertas, nessa ordem, levaram ao desenho atual:

1. **`notification_url` definida na criação da preferência tem prioridade sobre a URL configurada no painel** — e, segundo a documentação do próprio Mercado Pago, notificações entregues por esse caminho **não podem ser validadas com `x-signature`**, não importa qual chave secreta seja usada. Nosso código chegou a mandar `notification_url` na preferência; isso foi removido — a URL do painel (a única assinada) passou a ser a única fonte configurada.
2. **Mesmo com o painel corretamente configurado** (confirmado batendo o botão "Simular notificação", que retornou `200 OK` de verdade), **pagamentos reais no ambiente de teste não disparavam notificação nenhuma** pro webhook — nem chegando e falhando na assinatura, simplesmente não chegava nada. Esse é um comportamento relatado como inconsistente por outros desenvolvedores integrando com o Mercado Pago em ambiente de teste, não um erro identificado no nosso código.

Dado isso, o **callback do retorno do checkout** (§7.1, passo 5) virou o caminho confiável de confirmação — ele não depende de nenhuma notificação assíncrona do lado do Mercado Pago, só do redirect que já acontece naturalmente como parte do Checkout Pro. A segurança dele vem da **reverificação via API autenticada** (mesmo princípio do webhook: nunca confiar em dado que chega de fora sem confirmar na fonte), não de uma assinatura.

O webhook continua implementado e funcional (a validação de assinatura funciona, como provado pela simulação) — fica como reforço para quando a entrega de notificação real se mostrar mais confiável (possivelmente distinto em produção) ou para reconciliação futura.

### 7.5 Validação de assinatura do webhook

Header `x-signature` no formato `ts=<timestamp>,v1=<hash>`. Manifesto assinado:

```
id:<data.id em minúsculo>;request-id:<x-request-id>;ts:<ts>;
```

`HMAC-SHA256(manifest, MP_WEBHOOK_SECRET)` deve bater com `v1`, comparado com `hmac.compare_digest` (comparação em tempo constante, evita timing attack). Requisição sem assinatura válida recebe `401` e não é processada — **esse check nunca deve ser contornado**, mesmo temporariamente para debug; é a única defesa contra alguém forjar confirmação de doação falsa por esse caminho específico.

### 7.6 Testando localmente

O webhook precisa de uma URL pública (o Mercado Pago não alcança `localhost`). Em desenvolvimento, isso é feito via túnel (`ngrok` ou `cloudflared`) apontando pra porta 8000. A URL muda a cada reinício do túnel no plano gratuito — nesses casos, é preciso atualizar `PUBLIC_BACKEND_URL` no `.env`, **recriar o container** (`docker compose up -d --force-recreate backend` — `restart` sozinho não recarrega `.env`), e reconfigurar a URL no painel do Mercado Pago.

O caminho de callback (§7.4) pode ser testado sem nem completar um pagamento novo, batendo direto na rota com um `payment_id` de um pagamento já aprovado:
```bash
curl "http://localhost:8000/api/v1/donations/callback?payment_id=<id>&external_reference=<uuid-da-doacao>"
```

Cartão de teste (Brasil, força aprovação com o nome do titular `APRO`):
```
Número: 5480 8328 0103 3311
Validade: 11/30
CVV: 123
Titular: APRO
CPF: 123.456.789-09
```

### 7.7 Lição de depuração: nível de log padrão do Python

Durante o debug dessa integração, um `logger.info(...)` usado pra diagnosticar o callback nunca aparecia nos logs — não porque o código não rodava, mas porque o nível de log padrão do Python é `WARNING`, e mensagens `INFO` são silenciosamente descartadas sem configuração explícita. Os logs de debug do webhook (`_verify_signature`) sempre usaram `logger.warning(...)` por esse motivo, e é o padrão a seguir em qualquer log de diagnóstico temporário neste projeto — `logger.info` só é confiável se o nível de logging for configurado explicitamente em algum lugar (o que ainda não fizemos).

### 7.8 Pendências conhecidas desta integração

- O `back_url` do checkout aponta hoje pra uma página HTML simples servida pelo próprio backend (`GET /donations/callback`) — quando o fluxo for ligado ao app mobile de verdade, isso deve virar um deep link (`stray://...`), com a mesma lógica de reverificação rodando no app em vez de numa página web.
- Sem verificação de e-mail no cadastro de usuário — não é específico de pagamento, mas relevante pra quem vai doar.
- Sem revogação de refresh token — não afeta pagamento diretamente, mas é uma pendência de segurança geral já registrada.
- Investigar com o suporte do Mercado Pago por que notificações de pagamento real não chegam em ambiente de teste, mesmo com o painel corretamente configurado — vale confirmar se produção se comporta diferente antes de decidir se o webhook algum dia volta a ser o caminho primário.

---

## 8. Frontend (Expo / React Native / TypeScript)

### 8.1 Estrutura

```
frontend/
├── App.tsx                    — ponto de entrada, navegação por abas, sessão
├── LoginScreen.tsx
├── MapScreen.tsx               — mapa com sightings, criação e detalhe
├── AnimalsScreen.tsx           — lista de animais, criação e detalhe
├── CreateSightingModal.tsx
├── SightingDetailModal.tsx
├── CreateAnimalModal.tsx
├── AnimalDetailModal.tsx
└── lib/
    ├── api.ts                 — cliente HTTP tipado (todas as chamadas à API)
    ├── auth-storage.ts        — tokens no expo-secure-store (nunca AsyncStorage puro)
    └── auth-client.ts         — wrapper com renovação automática de sessão
```

### 8.2 Navegação

`@react-navigation/native` + `@react-navigation/bottom-tabs`, duas abas: **Mapa** e **Animais**. Introduzida quando o app passou a ter mais de uma tela "raiz" — telas secundárias (criar relato, detalhe de animal) continuam sendo modais, não rotas.

### 8.3 Bibliotecas nativas principais

`react-native-maps`, `expo-location` (mapa e geolocalização), `expo-secure-store` (armazenamento seguro de token).

### 8.4 Padrão de tela com modal

Cada recurso (`sightings`, `animals`) segue o mesmo padrão: tela de lista/mapa → toca num item → modal de detalhe → edição inline sem precisar de tela separada. Ações que só o dono pode fazer (editar, remover) checam `currentUserId === item.reporter_id/registered_by` no cliente **só por UX** — a autorização de verdade é sempre reforçada no backend.

---

## 9. O que ainda não existe

Registrado aqui de propósito, para não ser confundido com bug:

- **Matching de fotos por IA** (pgvector): schema pronto (`photo_embedding`), worker de geração de embedding não construído.
- **`feeding-points`, `moderation`, `chat`, `media`**: rotas declaradas, sem lógica implementada (retornam `501`).
- **Upload de mídia real**: bucket MinIO provisionado, endpoints `/media/*` ainda stub.
- **Verificação de e-mail** no cadastro.
- **Revogação de refresh token** (ex: ao trocar senha).
- **Deep link** de retorno do checkout de pagamento pro app mobile.
- **Rotina de anonimização** de `DELETE /users/me`.

---

## 10. Convenções do projeto

- Toda tabela nova precisa ser registrada em `app/models/__init__.py` — é assim que o Alembic autogenerate a enxerga.
- Todo modelo com coluna `Enum` novo, se adicionado via `ALTER TABLE` (não `CREATE TABLE`), precisa do fix de `create_type=False` manual na migration (§2.4.2).
- Todo endpoint de escrita (`POST`/`PATCH`/`DELETE`) que opera sobre um recurso "de alguém" segue o padrão **dono ou moderador**.
- Dinheiro é sempre `Numeric`, nunca `Float`.
- Toda resposta pública de geolocalização passa por arredondamento — nunca expor coordenada bruta do banco.

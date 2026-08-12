# App de animais de rua — ambiente local

## Pré-requisitos

- Docker + Docker Compose
- Node.js (LTS) e npm, para o frontend
- Opcional: `mc` (MinIO client) para criar o bucket via linha de comando

## 1. Subir a infraestrutura + backend

```bash
cp backend/.env.example backend/.env

docker compose up -d --build
```

A primeira build demora um pouco mais (instala o PostGIS via apt na imagem do Postgres).

## 2. Validar que tudo subiu certo

```bash
curl http://localhost:8000/health
```

Resposta esperada (a versão do PostGIS pode variar):

```json
{
  "database": "ok",
  "postgis": "3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1",
  "pgvector": "ok",
  "redis": "ok"
}
```

Se `pgvector` ou `postgis` vierem com erro, rode `docker compose logs db` — geralmente é
porque o nome do pacote `postgresql-16-postgis-3` mudou de versão no repositório
apt; ajuste o Dockerfile em `docker/postgres/Dockerfile` conforme a mensagem de erro.

## 3. Criar o bucket no MinIO (armazenamento de mídia local)

Acesse o console em [http://localhost:9001](http://localhost:9001)
(login: `minioadmin` / senha: `minioadmin`) e crie um bucket chamado `animal-media`.

Ou via `mc`:

```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/animal-media
```

## 4. Criar o projeto frontend (React Native com Expo)

```bash
npx create-expo-app frontend
cd frontend

npx expo install react-native-maps expo-location expo-image-picker
```

Rodar:

```bash
npx expo start
```

## Estrutura do repositório

```
.
├── docker-compose.yml
├── docker/postgres/       # Dockerfile + init.sql (PostGIS + pgvector)
├── backend/                # FastAPI
│   └── app/
│       ├── core/config.py  # variáveis de ambiente
│       ├── db/session.py   # engine + sessão async do SQLAlchemy
│       ├── models/         # modelos ORM (stub do Sighting já com Geography + Vector)
│       └── main.py         # app FastAPI + /health
└── frontend/                # criado no passo 4 (Expo)
```

## Próximos passos

- Configurar o Alembic para migrations versionadas (o modelo `Sighting` em
  `app/models/sighting.py` ainda não gerou tabela nenhuma — é só um exemplo dos tipos).
- Automatizar a criação do bucket do MinIO no `docker-compose.yml`
  (serviço auxiliar `mc` rodando uma vez na subida).
- Implementar os endpoints reais de autenticação, relatos e upload de mídia.

## Nota sobre versões

As versões em `backend/requirements.txt` estão fixadas como mínimas (`>=`), não exatas.
Rode `pip list --outdated` depois de instalar para conferir se há versões mais
recentes disponíveis no momento em que você for de fato configurar isso.

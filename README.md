# VASQ-AI# VASQ AI

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20%7C%20Qwen3-000000)

> Plataforma de IA modular con FastAPI y Clean Architecture. El modelo de lenguaje es intercambiable: Ollama/Qwen 3 hoy, OpenAI, Claude o Gemini mañana.

**Autor:** Juan Felipe Vásquez · VASQTECH

Plataforma de IA modular y escalable — núcleo de VASQTECH.

Construida siguiendo Clean Architecture, con un modelo open source (Qwen 3
vía Ollama) corriendo localmente, y preparada para sustituir el proveedor
de IA por GPT, Claude, Gemini u otro sin tocar la lógica de negocio.

## Estado: Módulos 1–7 completos

| # | Módulo | Contenido |
|---|--------|-----------|
| 1 | Bootstrap | Estructura Clean Architecture, config, Docker, conexión a PostgreSQL |
| 2 | LLM Provider | Interfaz `LLMProvider` + `OllamaProvider` (Qwen 3) + factory intercambiable |
| 3 | Auth | Registro, login, JWT (access + refresh tokens), hashing con bcrypt |
| 4 | API Keys | Generación, listado, revocación, scopes, guardado hasheado |
| 5 | Chat | Endpoint de chat + memoria conversacional persistida en PostgreSQL |
| 6 | Docker | `docker-compose.yml` con app + PostgreSQL + Redis + Ollama, migraciones automáticas al arrancar |
| 7 | Módulos futuros | Esqueleto `app/modules/` con `trading` como ejemplo de referencia |

## Hoja de ruta

- [x] Núcleo: auth, API Keys, chat con memoria, proveedor de IA intercambiable
- [ ] Módulo `trading` (hoy solo un ejemplo de referencia)
- [ ] Módulo `finance`
- [ ] Módulo `news`
- [ ] Módulo `documents`
- [ ] Proveedores OpenAI, Anthropic y Gemini completos

## Arquitectura

```
app/
├── domain/ports/llm_provider.py   ← interfaz LLMProvider (pieza central)
├── infrastructure/
│   ├── llm/                        ← OllamaProvider, OpenAIProvider (stub), factory
│   └── db/                         ← modelos SQLAlchemy, sesión async
├── application/
│   ├── services/                   ← AuthService, APIKeyService, ChatService, MemoryService
│   └── schemas/                    ← DTOs Pydantic
├── api/v1/routers/                 ← auth, api_keys, chat, health
├── modules/                        ← trading (ejemplo), finance, news, documents (vacíos, listos para crecer)
└── core/                           ← config, security (JWT/hashing), logging
```

**La decisión de arquitectura más importante**: nada fuera de
`infrastructure/llm/` sabe que existe Ollama o Qwen 3. Todo el sistema
programa contra la interfaz `LLMProvider`. Cambiar de modelo en el futuro
es: escribir `anthropic_provider.py` implementando esa interfaz, añadir un
`elif` en `factory.py`, y cambiar `LLM_PROVIDER=anthropic` en `.env`. Cero
cambios en servicios, routers o memoria conversacional.

## Cómo levantarlo

1. Copia el archivo de entorno y genera un secreto JWT propio:

   ```bash
   cp .env.example .env
   # Edita JWT_SECRET_KEY en .env con un valor largo y aleatorio
   ```

2. Levanta todo con Docker (construye la app, aplica migraciones
   automáticamente al arrancar, y levanta PostgreSQL, Redis y Ollama):

   ```bash
   docker compose up --build
   ```

3. Descarga el modelo Qwen 3 dentro del contenedor de Ollama (una sola vez):

   ```bash
   docker exec -it vasq_ai_ollama ollama pull qwen3
   ```

4. Explora la API interactiva (Swagger UI generado automáticamente):

   ```
   http://localhost:8000/docs
   ```

## Flujo típico de uso

```bash
# 1. Registro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"tu@email.com","password":"tu-password-segura"}'

# 2. Login → obtienes access_token y refresh_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tu@email.com","password":"tu-password-segura"}'

# 3. Chat (usando el access_token del paso anterior)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola, ¿qué puedes hacer?"}'

# 4. (Opcional) Crear una API Key para integraciones externas
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"integración n8n","scopes":["chat:read","chat:write"]}'
```

## Correr sin Docker (desarrollo local)

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ajusta DATABASE_URL y OLLAMA_BASE_URL a localhost
alembic upgrade head
uvicorn app.main:app --reload
```

Necesitas PostgreSQL y Ollama corriendo localmente (con `ollama pull qwen3`
ya ejecutado).

## Tests

```bash
pytest
```

## Cómo añadir un módulo de negocio nuevo (trading, finance, news, documents...)

Sigue el patrón de `app/modules/trading/router.py`:

1. Crea `app/modules/<nombre>/router.py` con tu propio `APIRouter`.
2. Reutiliza `get_current_active_user`, `get_db`, `get_llm_provider` por
   inyección de dependencias — nunca reimplementes auth o acceso a datos.
3. Regístralo en `app/main.py` con una línea: `app.include_router(...)`.
4. Si el módulo necesita sus propias tablas, crea sus modelos en
   `app/infrastructure/db/models_<nombre>.py`, impórtalos en `models.py`,
   y genera una migración con `alembic revision --autogenerate -m "..."`.

## Cómo cambiar de proveedor de IA en el futuro

1. Implementa la interfaz en `app/infrastructure/llm/<proveedor>_provider.py`
   (ver `openai_provider.py` como plantilla ya preparada).
2. Añade el `elif` correspondiente en `app/infrastructure/llm/factory.py`.
3. Añade sus variables de config en `app/core/config.py` y `.env.example`.
4. Cambia `LLM_PROVIDER=<proveedor>` en `.env`.

Ningún servicio, router, ni la memoria conversacional necesitan cambios.

## Notas de seguridad para producción

- Cambia `JWT_SECRET_KEY` por un valor largo y aleatorio (nunca uses el de
  `.env.example`).
- Las API Keys y contraseñas se guardan siempre hasheadas (bcrypt) —
  ninguna se puede recuperar en texto plano después de creada.
- Considera añadir rate limiting (Redis ya está disponible en el stack)
  antes de exponer la API públicamente.
- Revisa los scopes de las API Keys según el consumidor (no repartas
  `chat:write` a integraciones que solo necesitan leer).

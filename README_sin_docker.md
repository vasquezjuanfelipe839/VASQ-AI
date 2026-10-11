# VASQ AI

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20%7C%20Qwen3-000000)

> Plataforma de IA modular con FastAPI y Clean Architecture. El modelo de lenguaje es intercambiable: Ollama/Qwen 3 hoy, OpenAI, Claude o Gemini mañana.

**Autor:** Juan Felipe Vásquez · VASQTECH

Plataforma de IA modular y escalable — núcleo de VASQTECH.

Construida siguiendo Clean Architecture, con un modelo open source (Qwen 3
vía Ollama) corriendo localmente, y preparada para sustituir el proveedor
de IA por GPT, Claude, Gemini u otro sin tocar la lógica de negocio.

## Estado: Módulos 1–6 completos

| # | Módulo | Contenido |
|---|--------|-----------|
| 1 | Bootstrap | Estructura Clean Architecture, config, conexión a PostgreSQL |
| 2 | LLM Provider | Interfaz `LLMProvider` + `OllamaProvider` (Qwen 3) + factory intercambiable |
| 3 | Auth | Registro, login, JWT (access + refresh tokens), hashing con bcrypt |
| 4 | API Keys | Generación, listado, revocación, scopes, guardado hasheado |
| 5 | Chat | Endpoint de chat + memoria conversacional persistida en PostgreSQL |
| 6 | Módulos futuros | Esqueleto `app/modules/` con `trading` como ejemplo de referencia |

## Hoja de ruta

- [x] Núcleo: auth, API Keys, chat con memoria, proveedor de IA intercambiable
- [ ] Docker y `docker-compose.yml` (app + PostgreSQL + Redis + Ollama)
- [ ] Más pruebas automatizadas (hoy solo hay una prueba de health check)
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

## Cómo levantarlo (desarrollo local)

Necesitas Python 3.13, PostgreSQL y, para el endpoint de chat, Ollama.

1. Crea el entorno virtual e instala las dependencias:

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate      # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Crea la base de datos en PostgreSQL (estos son los valores por defecto;
   se pueden cambiar con `DATABASE_URL`):

   ```sql
   CREATE USER vasq WITH PASSWORD 'vasq';
   CREATE DATABASE vasq_ai OWNER vasq;
   ```

3. (Opcional) Cambia la configuración. Todas las variables tienen un valor
   por defecto en `app/core/config.py`. Para sobrescribirlas, crea un archivo
   `.env` en la raíz del proyecto (nunca lo subas a GitHub):

   ```
   APP_ENV=local
   DEBUG=true

   # Cambia este valor por uno largo y aleatorio
   JWT_SECRET_KEY=cambia-esto-por-un-valor-largo-y-aleatorio
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

   API_KEY_PREFIX=vasq_
   DATABASE_URL=postgresql+psycopg://vasq:vasq@localhost:5432/vasq_ai

   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen3
   ```

   El valor por defecto de `JWT_SECRET_KEY` es solo un marcador
   (`CHANGE_ME_IN_ENV`): cámbialo siempre fuera de desarrollo.

4. Aplica las migraciones:

   ```bash
   alembic upgrade head
   ```

5. Descarga el modelo en Ollama (una sola vez) y deja Ollama corriendo:

   ```bash
   ollama pull qwen3
   ```

6. Arranca la API:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Explora la API interactiva (Swagger UI generado automáticamente):

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

# 3. Chat (usando el access_token del paso anterior; requiere Ollama corriendo)
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

Si Ollama no está corriendo, el paso 3 responde con un error controlado
("El modelo de IA no pudo responder"); el resto de los pasos no lo necesita.

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
3. Añade sus variables de config en `app/core/config.py` y en tu `.env`.
4. Cambia `LLM_PROVIDER=<proveedor>` en `.env`.

Ningún servicio, router, ni la memoria conversacional necesitan cambios.

## Notas de seguridad para producción

- Cambia `JWT_SECRET_KEY` por un valor largo y aleatorio (nunca dejes el
  valor por defecto `CHANGE_ME_IN_ENV`).
- Las API Keys y contraseñas se guardan siempre hasheadas (bcrypt) —
  ninguna se puede recuperar en texto plano después de creada.
- Considera añadir rate limiting (la configuración de Redis ya está prevista
  en `app/core/config.py`) antes de exponer la API públicamente.
- Revisa los scopes de las API Keys según el consumidor (no repartas
  `chat:write` a integraciones que solo necesitan leer).

# P2M-TAI Tech Stack

Complete list of all technologies used in the project.

---

## FRONTEND (apps/web)

### Core Framework
| Technology | Version | Purpose |
|------------|---------|----------|
| **Next.js** | latest | React framework, SSR/SSG |
| **React** | latest | UI library |
| **React DOM** | latest | React rendering |
| **TypeScript** | latest | Type safety |

### Styling & UI
| Technology | Version | Purpose |
|------------|---------|----------|
| **Tailwind CSS** | ^4.2.2 | Utility-first CSS framework |
| **shadcn** | ^4.1.0 | UI component library |
| **Base-UI React** | ^1.3.0 | Component primitives |
| **Lucide React** | ^1.6.0 | Icon library |
| **class-variance-authority** | ^0.7.1 | Component variants |
| **tw-animate-css** | ^1.4.0 | CSS animations |
| **@tailwindcss/postcss** | ^4.2.2 | PostCSS for Tailwind |

### Utilities
| Technology | Version | Purpose |
|------------|---------|----------|
| **tailwind-merge** | ^3.5.0 | Merge Tailwind classes |
| **clsx** | ^2.1.1 | Conditional classNames |

### Database & Auth
| Technology | Version | Purpose |
|------------|---------|----------|
| **@supabase/supabase-js** | latest | Supabase client |

### Build Tools
| Technology | Version | Purpose |
|------------|---------|----------|
| **PostCSS** | ^8.4.31 | CSS transformation |
| **@types/node** | latest | Node types |

---

## BACKEND (apps/api)

### Web Framework
| Technology | Version | Purpose |
|------------|---------|----------|
| **FastAPI** | >=0.115.0 | Python web framework |
| **uvicorn** | >=0.30.0 | ASGI server |
| **pydantic** | >=2.8.0 | Data validation |
| **python-multipart** | >=0.0.9 | File uploads |
| **python-dotenv** | >=1.0.1 | Environment variables |
| **requests** | >=2.32.0 | HTTP client |

### AI & LLM
| Technology | Version | Purpose |
|------------|---------|----------|
| **Mistral AI** | >=1.5.0 | LLM provider |
| **Groq** | >=0.4.0 | LLM provider |
| **LangChain** | >=0.3.0 | LLM orchestration |
| **LangChain Groq** | >=0.2.0 | Groq LangChain integration |
| **LangChain HuggingFace** | >=0.1.0 | HuggingFace integration |

### NLP & Text Processing
| Technology | Version | Purpose |
|------------|---------|----------|
| **spaCy** | >=3.7.5 | NLP processing |
| **Chonkie** | >=0.3.0 | Text chunking for RAG |
| **langdetect** | >=1.0.9 | Language detection |
| **deep-translator** | >=1.11.4 | Translation API |
| **python-docx** | >=0.8.11 | Word document parsing |

### Database & Storage
| Technology | Version | Purpose |
|------------|---------|----------|
| **supabase** | >=2.7.4 | Database client |

### Messaging & Queue
| Technology | Version | Purpose |
|------------|---------|----------|
| **Pika** | >=1.3.2 | RabbitMQ client |
| **Redis** | >=5.0.8 | Cache & queue |

### Email
| Technology | Version | Purpose |
|------------|---------|----------|
| **SendGrid** | >=6.11.0 | Email service |

---

## PROJECT STRUCTURE

```
P2M-TAI/
├── apps/
│   ├── api/           # FastAPI backend
│   │   └── requirements.txt
│   └── web/           # Next.js frontend
│       ├── package.json
│       └── src/
│           ├── app/              # Next.js App Router
│           ├── components/        # React components
│           │   ├── layout/        # Layout components
│           │   ├── ui/           # shadcn UI components
│           │   └── upload/       # Upload components
│           └── lib/             # Utilities & API clients
│               └── api/          # API client functions
├── packages/
│   ├── shared-types/  # TypeScript types
│   └── ui/           # Shared UI package
├── docs/             # Documentation
└── package.json     # Monorepo config
```

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  App Router  │  │ shadcn/ui    │  │  API Client     │   │
│  │  Pages/SSR   │  │ Components   │  │  (tenders.ts)  │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (HTTP/REST)
┌─────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  Documents  │  │   RAG/AI    │  │  Compliance    │   │
│  │  Routes     │  │  Pipeline   │  │  Engine        │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  LangChain  │  │   LLM's     │  │  Database       │   │
│  │  Pipeline   │  │ (Mistral)  │  │  (Supabase)     │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## KEY INTEGRATIONS

### LLM Providers
- **Mistral AI** - Primary LLM for response generation
- **Groq** - Fast inference for RAG queries

### RAG Pipeline
1. **Document Upload** → PDF/DOCX parsing (python-docx)
2. **Text Extraction** → spaCy for NLP, Chonkie for chunking
3. **Embedding** → LangChain + HuggingFace embeddings
4. **Vector Store** → (configured in LangChain)
5. **Retrieval** → Similarity search
6. **Generation** → LLM (Mistral/Groq) with context

### Database
- **Supabase** - PostgreSQL + Auth + Storage

### Queue/Async
- **Redis** - Caching, session management
- **RabbitMQ (via Pika)** - Async task processing

---

## DEVELOPMENT TOOLS

- **TypeScript** - Type safety across frontend
- **Tailwind CSS v4** - Modern CSS utility classes
- **shadcn/ui** - Accessible, customizable UI components
- **Next.js App Router** - Modern React SSR

---

## ENVIRONMENT VARIABLES

Frontend (`apps/web/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8100
```

Backend (`apps/api/.env`):
```
SUPABASE_URL=...
SUPABASE_KEY=...
MISTRAL_API_KEY=...
GROQ_API_KEY=...
REDIS_URL=...
RABBITMQ_URL=...
```

---

## SUMMARY BY CATEGORY

| Category | Technologies |
|----------|--------------|
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python, uvicorn |
| **AI/LLM** | Mistral AI, Groq, LangChain, spaCy |
| **Database** | Supabase (PostgreSQL) |
| **Queue** | Redis, RabbitMQ (Pika) |
| **NLP** | spaCy, Chonkie, langdetect |
| **Email** | SendGrid |
| **Icons** | Lucide React |
| **Styling** | Tailwind CSS v4, Base-UI |
# Architecture

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Plotly.js for charts

## Backend

- FastAPI
- Python
- Pydantic settings and schemas
- SQLAlchemy for relational persistence

## Datastores

- PostgreSQL for document metadata, users, matters, audit logs, entities, classifications, and relationships.
- Qdrant for vector search and RAG retrieval.

## AI Components

- Embeddings through OpenAI, Azure OpenAI, or local sentence-transformer models.
- LLM workflows for cited answers, summaries, classification explanations, and investigation assistance.
- NLP through spaCy or transformer models for named entity recognition and relationship extraction.

## Initial Service Boundaries

- `ingestion` - accepts files, extracts text, stores metadata.
- `classification` - labels documents using rules first, ML later.
- `entities` - extracts and normalizes named entities.
- `search` - coordinates keyword, metadata, vector, and citation search.
- `analytics` - computes dashboard metrics and timeline data.
- `evaluation` - tracks retrieval, extraction, classification, and answer quality.

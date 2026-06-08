# Next Steps

## Recommended Build Order

1. Create the first database models for matters and documents.
2. Implement document upload persistence.
3. Add PDF text extraction with `pypdf`.
4. Store extracted metadata and parsing status.
5. Build the frontend upload workflow.
6. Add document list filters for file type, custodian, and classification.
7. Create synthetic sample data for repeatable testing.

## Early Product Decisions

- Decide whether the first demo matter should use synthetic emails, contracts, pleadings, or a blended sample production.
- Decide whether OpenAI embeddings or local sentence-transformers should be the initial embedding provider.
- Decide whether authentication is needed for the first prototype or can wait until after ingestion and search.

## First Useful Demo

A strong first demo would let a user upload a small synthetic production, see metadata populate, search across parsed text, and view basic dashboard counts.

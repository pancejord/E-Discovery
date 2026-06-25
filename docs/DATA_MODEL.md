# Data Model

Date: 2026-06-23

This reference summarizes the implemented SQLAlchemy models in `backend/app/models`.

## Matter

- `id`: primary key
- `name`: indexed matter name
- `description`: optional text description
- `client_name`: optional indexed client name
- `matter_number`: optional unique indexed matter number
- `ai_external_allowed`: whether external AI providers may be used for this matter
- `ai_redaction_required`: whether prompts/sources must be redacted before external provider calls
- `ai_allowed_modes`: JSON list of enabled assistant modes for the matter
- `created_at`: UTC creation timestamp
- Relationships: `documents`, `memberships`

## Custodian

- `id`: primary key
- `full_name`: indexed custodian name
- `email`: optional unique indexed email
- `organization`: optional indexed organization
- `role`: optional role/title
- `created_at`: UTC creation timestamp
- Relationships: `documents`

## Document

- `id`: primary key
- `matter_id`: optional indexed foreign key to `matters.id`
- `custodian_id`: optional indexed foreign key to `custodians.id`
- `parent_document_id`: optional indexed self-reference for child attachment documents
- `attachment_filename`: optional indexed original attachment filename
- `original_filename`: source upload name
- `stored_file_path`: stored upload path
- `file_type`: indexed file extension/type
- `document_type`: optional indexed rule-based classification
- `extracted_text`: extracted document text
- `text_hash`: optional indexed text hash
- `extraction_warnings`: serialized warnings from parsing/OCR/attachments
- `attachment_names`: serialized attachment inventory
- `ocr_status`: optional indexed OCR state
- `sender`, `recipients`, `cc`, `bcc`: email metadata fields
- `subject`: optional indexed subject/title
- `document_date`: optional indexed normalized document date
- `tags`: serialized review tags
- `notes`: reviewer notes
- `issue_codes`: serialized issue codes
- `privilege_flag`: indexed privilege flag
- `review_status`: indexed review status
- `created_at`: UTC creation timestamp
- `processing_status`: indexed status such as `uploaded`, `parsed`, or `needs_ocr`
- `processing_stages`: JSON processing-stage map
- `processing_error`: latest processing/reprocessing error
- `risk_score`: numeric risk score placeholder
- Relationships: `matter`, `custodian`, `parent_document`, `child_documents`, `chunks`, `entity_mentions`, `relationships`

## Document Chunk

- `id`: primary key
- `document_id`: foreign key to `documents.id`
- `chunk_index`: chunk order within document
- `text`: chunk text
- `text_hash`: chunk hash
- `char_start`, `char_end`: character offsets in source text
- `token_count`: estimated token count
- `vector_id`: optional vector-store point id
- `embedding`: serialized local embedding
- `embedding_model`: embedding provider/model name
- `created_at`: UTC creation timestamp

## Entity

- `id`: primary key
- `matter_id`: optional indexed matter scope
- `name`: display name
- `entity_type`: indexed type such as person, organization, email, or date
- `normalized_name`: indexed deduplication key
- `alias_of_entity_id`: optional self-reference when an entity is merged into another entity
- `review_status`: indexed entity review state such as `unreviewed`, `reviewed`, or `merged`
- `extraction_provider`: provider that created the entity, such as `deterministic`, `spacy`, or `review_split`
- `created_at`: UTC creation timestamp

## Entity Mention

- `id`: primary key
- `entity_id`: foreign key to `entities.id`
- `document_id`: foreign key to `documents.id`
- `chunk_id`: optional foreign key to `document_chunks.id`
- `mention_text`: exact mention text
- `char_start`, `char_end`: character offsets
- `citation`: source citation string
- `created_at`: UTC creation timestamp

## Relationship

- `id`: primary key
- `matter_id`: optional indexed matter scope
- `source_entity_id`: source entity foreign key
- `relationship_type`: indexed type, including `mentioned_with`, `communicated_with`, `associated_with`, `monetary_reference`, `legal_reference`, `located_in`, and `dated_event`
- `target_entity_id`: target entity foreign key
- `document_id`: optional source document foreign key
- `confidence`: numeric confidence
- `evidence`: supporting evidence snippet
- `confidence_explanation`: short explanation of why the confidence score was assigned
- `created_at`: UTC creation timestamp

## Saved Search

- `id`: primary key
- `matter_id`: optional indexed matter scope
- `name`: indexed saved-search name
- `query`: saved query text
- `filters`: JSON metadata filters
- `created_by`: optional indexed actor
- `is_shared`: indexed saved-search sharing flag
- `created_at`: UTC creation timestamp
- `updated_at`: last update timestamp

## Audit Log

- `id`: primary key
- `actor`: optional indexed actor name/email
- `action`: indexed event action
- `matter_id`: optional indexed matter id
- `document_id`: optional indexed document id
- `entity_id`: optional indexed entity id
- `request_id`: optional indexed request/correlation id
- `client_ip`: optional indexed client IP
- `user_agent`: optional request user agent
- `route`: optional indexed route/path
- `method`: optional indexed HTTP method
- `response_status`: optional indexed HTTP response status
- `summary`: human-readable event summary
- `details`: JSON event details
- `created_at`: UTC event timestamp

## Role

- `id`: primary key
- `name`: unique indexed role name
- `description`: optional role description
- `is_admin`: grants admin-only endpoints when true
- `created_at`: UTC creation timestamp
- Relationships: `users`

## User

- `id`: primary key
- `email`: unique indexed email
- `display_name`: display name
- `api_key_hash`: unique indexed SHA-256 API-key hash
- `role_id`: optional indexed foreign key to `roles.id`
- `organization`: optional indexed organization/client grouping
- `tenant_id`: optional indexed tenant identifier
- `is_active`: indexed active/deactivated flag
- `created_at`: UTC creation timestamp
- Relationships: `role`, `memberships`

## Matter Membership

- `id`: primary key
- `user_id`: indexed foreign key to `users.id`
- `matter_id`: indexed foreign key to `matters.id`
- `role`: matter-specific assignment role
- `created_at`: UTC creation timestamp
- Constraint: unique `(user_id, matter_id)`
- Relationships: `user`, `matter`

## Evaluation Run

- `id`: primary key
- `matter_id`: optional indexed matter scope
- `dataset_name`: indexed benchmark dataset
- `case_id`: optional indexed benchmark case id
- `task_type`: indexed task type such as retrieval, answer, extraction, or comparison
- `metric_name`: indexed metric name
- `metric_value`: numeric metric value
- `details`: JSON metric context, including benchmark owner and triage notes when provided
- `created_at`: UTC creation timestamp

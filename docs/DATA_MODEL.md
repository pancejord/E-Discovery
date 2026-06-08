# Data Model Draft

## Matter

- `id`
- `name`
- `description`
- `created_at`

## Document

- `id`
- `matter_id`
- `title`
- `filename`
- `file_type`
- `file_size`
- `created_date`
- `modified_date`
- `sender`
- `recipients`
- `subject`
- `custodian`
- `text_status`
- `classification`
- `created_at`

## Entity

- `id`
- `matter_id`
- `name`
- `entity_type`
- `normalized_name`

## Relationship

- `id`
- `matter_id`
- `source_entity_id`
- `relationship_type`
- `target_entity_id`
- `document_id`
- `confidence`

## Chunk

- `id`
- `document_id`
- `chunk_index`
- `text`
- `vector_id`

## Evaluation Run

- `id`
- `matter_id`
- `task_type`
- `metric_name`
- `metric_value`
- `created_at`

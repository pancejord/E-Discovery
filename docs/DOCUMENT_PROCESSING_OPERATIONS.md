# Document Processing Operations

Date: 2026-06-25

This note describes the current first-pass production document-processing workflow: OCR setup, supported formats, attachment lineage, processing stages, and reprocessing controls.

## OCR Toolchain

PDF OCR is optional and command-driven so local development can run without heavy OCR dependencies.

Enable OCR with environment settings:

```text
OCR_ENABLED=true
OCR_PDF_TO_TEXT_COMMAND=<command that writes extracted text to stdout and accepts {input}>
```

The command must include `{input}` where the uploaded PDF path should be inserted. A local deployment can wrap OCRmyPDF/Tesseract behind a small script that writes OCR text to stdout. Example shape:

```text
OCR_PDF_TO_TEXT_COMMAND=python scripts/ocr_pdf_to_stdout.py {input}
```

If OCR is disabled or the configured command fails, scanned PDFs keep a clear `ocr_status` and `extraction_warnings` value so reviewers can see that OCR did not complete.

## Supported Extraction Formats

Current extraction support includes:

- Text-like files: `txt`, `md`, `csv`, `tsv`, `log`
- Documents: `pdf`, `docx`
- Email: `eml`
- Lightweight web/rich text/spreadsheet/archive handling: `html`, `htm`, `rtf`, `xlsx`, `zip`

The HTML, RTF, XLSX, and ZIP handlers are lightweight standard-library extractors intended to make common productions searchable. They are not a full replacement for specialist forensic email/archive tooling.

## Attachment Lineage

Supported attachments inside `eml` files are persisted as child `documents` rows.

Child attachment documents store:

- `parent_document_id`
- `attachment_filename`
- extracted text, warnings, OCR status, and document date when available
- their own chunks, vector indexing payloads, entity mentions, and relationships

The parent email still includes attachment inventory and extracted attachment text in its combined extracted text for convenience, but the child document row is now the durable lineage record.

## Processing Stages

Documents store processing state in `processing_stages` and the latest failure message in `processing_error`.

Expected stage keys include:

- `uploaded`
- `extracted`
- `ocr`
- `chunked`
- `indexed`
- `entity_extraction`
- `failed`

Stage values are simple status strings such as `completed`, `not_required`, `recommended`, or `failed`.

## Reprocess And Retry

Document processing can be rerun without direct database edits:

```text
POST /api/documents/{document_id}/reprocess
POST /api/documents/{document_id}/retry/{stage}
```

Accepted retry stages are:

- `extraction`
- `ocr`
- `indexing`
- `entity_extraction`
- `all`

The current retry endpoint performs a full rebuild for the selected document. Reprocessing clears derived chunks, entity mentions, and relationships for that document, then reruns extraction, chunking, vector indexing, and entity extraction from the stored file path.

## Current Limits

- PST and MSG are not yet natively parsed.
- Image-only documents rely on the configured PDF OCR flow rather than standalone image OCR.
- ZIP extraction currently creates searchable archive text and file inventory, but archive contents are not yet persisted as independent child document rows.
- Parent reprocessing reruns the parent document from its stored file. Existing child attachments can be reprocessed individually from their own document pages.
- Upload progress and large-file limit UX still need a more complete production pass.

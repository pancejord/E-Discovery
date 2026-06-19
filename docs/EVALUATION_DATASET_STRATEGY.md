# Evaluation Dataset Strategy

Date: 2026-06-19

## Recommendation

Start with richer synthetic legal-domain datasets before using real matter data.

For this project, the correct route is:

1. Synthetic benchmark productions.
2. Public or approved legal-like corpora, only if licensing and sensitivity are clear.
3. Sanitized real matter data, only after redaction, approval, access control, and audit logging are mature.

Do not use privileged, confidential, client, or production discovery data as the first evaluation dataset.

## Why Synthetic First

Synthetic datasets are safer and more controllable. They let the project test retrieval, citations, answer grounding, entity extraction, relationship extraction, and hallucination detection without risking sensitive data.

They also make regression testing easier because each document can be designed to contain known facts, known distractors, and expected citations.

## Recommended Dataset Shape

Each benchmark production should include:

- A dataset name and description.
- A set of synthetic documents.
- Retrieval benchmark cases.
- Generated-answer benchmark cases.
- Expected facts or terms.
- Expected citation count.
- Optional negative cases where the answer should say the documents do not establish the claim.

Useful synthetic document categories:

- Contract or amendment.
- Email thread.
- Invoice or payment record.
- Discovery response.
- Legal memo.
- Pleading or motion excerpt.
- Court order.
- Custodian chat export.

## Evaluation Tracks

### Retrieval Evaluation

Measure whether search finds the right source chunks.

Metrics:

- Retrieval precision.
- Retrieval recall.
- Citation coverage.
- Benchmark pass/fail.

### Answer Evaluation

Measure whether generated answers stay grounded in retrieved evidence.

Metrics:

- Citation count.
- Valid citation count.
- Unsupported term rate.
- Hallucination-risk score.

### Negative Evaluation

Measure whether the assistant refuses unsupported claims.

Examples:

- Ask for a payment amount not in the documents.
- Ask whether a person admitted liability when no source says that.
- Ask for a court ruling that is not present in the production.

## When To Use Real Data

Use real data only when all of these are true:

1. The dataset is approved for this purpose.
2. Confidential, privileged, and personally sensitive material has been reviewed.
3. The system has authentication, matter scoping, and audit logging enabled.
4. External AI calls are disabled or explicitly approved.
5. There is a documented retention and deletion plan.

## Immediate Next Step

Create a mixed synthetic production with multiple document types, expected retrieval cases, expected answer cases, and negative cases. Use that to harden the evaluation harness before bringing in any external corpus.

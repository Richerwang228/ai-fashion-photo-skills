---
name: openai-compatible-image-provider
description: Generate or edit project images only through the verified Right.codes asynchronous drawing API, using gpt-image-2 by default, local references, task polling, and local delivery. Use for every paid image generation in this project.
---

# Right.codes Image Provider

This is the project's only approved paid image transport. Domain skills decide
what to generate; this skill submits the approved prompt and references to
Right.codes, polls the returned task, downloads the result, and validates the
local image.

## Required client and configuration

Always use:

```text
.agents/scripts/right_codes_image_generator.py
```

The client reads process environment values first and then the project-root
`.env`. The required credential is `RIGHT_CODES_API_KEY`; never print it or
place it in prompts, manifests, logs, or source files. Optional overrides are:

```dotenv
RIGHT_CODES_BASE_URL=https://www.rightapi.ai/draw
RIGHT_CODES_MODEL=gpt-image-2
```

The verified defaults are already the values above. `RIGHT_API_KEY`,
`GEMINI_API_KEY`, and `IMAGE_API_KEY` remain compatibility fallbacks inside the
client, but project runs must select `RIGHT_CODES_API_KEY` explicitly.

## Verified protocol

- Submit exactly one JSON request to
  `POST https://www.rightapi.ai/draw/v1/images/generations`.
- The request always contains `async: true` and returns a `task_id`.
- Poll only that task at
  `GET https://www.rightapi.ai/v1/tasks/{task_id}`; the query endpoint does not
  contain `/draw`.
- Treat `queued` and `in_progress` as pending, `failed` as terminal failure, and
  a response containing `data` or `candidates` as completed output.
- Download URL or base64 results, verify PNG/JPEG/GIF/WebP signatures, and save
  locally before claiming success.

## Required workflow

Before the first paid call in a run:

1. Confirm the exact billable output count with the user.
2. Confirm every reference path exists and is assigned one narrow role.
3. Run the free credential check:

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  --check-auth \
  --credential-name RIGHT_CODES_API_KEY
```

4. Run `--dry-run` with the final model, aspect ratio, resolution, references,
   and output path.
5. Submit one output at a time with zero paid POST retries.

Example with references:

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "<approved prompt with exact reference roles>" \
  "/absolute/output/result.png" \
  1 \
  "/absolute/reference/model.png" \
  "/absolute/reference/top.png" \
  "/absolute/reference/bottom.png" \
  --credential-name RIGHT_CODES_API_KEY \
  --model gpt-image-2 \
  --size 4:5 \
  --image-size 1K \
  --timeout 600 \
  --poll-interval 3
```

For text-to-image, omit reference paths. `gpt-image-2` is limited to 1K on this
route. Do not request 2K or 4K for this model. Use another listed model only
after the user explicitly approves the different model and cost.

## Billing and recovery rules

1. A paid submission is never automatically retried.
2. Once a `task_id` exists, only poll or resume that exact task.
3. If polling is interrupted or times out, resume without another paid POST:

```bash
python3 .agents/scripts/right_codes_image_generator.py \
  "" \
  "/absolute/output/result.png" \
  1 \
  --resume-task "task_id_from_the_original_submission" \
  --credential-name RIGHT_CODES_API_KEY
```

4. If submission ends without a `task_id`, mark billing `INDETERMINATE`, check
   provider usage, and obtain renewed approval before any replacement request.
5. A completed download proves transport only. Run the calling domain skill's
   garment, anatomy, copy, and commercial QA before accepting the image.
6. Increase `n` or issue correction calls only after explicit paid-call approval.

## Verified project smoke test

On 2026-08-04, `gpt-image-2`, 1K, one text-to-image request completed through
Right.codes task polling and saved a valid 1254×1254 RGB PNG locally. This is a
transport smoke test, not proof that future garment references or commercial
outputs will pass visual QA.

## Reference order

For model-photo edits, preserve this default order unless the approved prompt
states a narrower role map:

1. approved model identity or worn master;
2. top front;
3. bottom front;
4. optional inner layer;
5. optional back or named detail references.

The prompt must say exactly which attributes each reference supplies and what
must be ignored.

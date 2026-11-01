# Qwen quantization study — compact handoff

This is the study input/result handoff, without a cloud-provider tutorial, dashboard, or energy-monitoring setup. Model weights are not bundled; their exact download revision, filenames, sizes and hashes are in model-manifest.json. Local machine paths are deliberately absent from core-config.json.

## Study and model

Measure how progressively stronger quantization changes demonstrated correctness and types of failure. Q8 is a quantized reference, not full-precision ground truth. Preserve improvements at lower precision as well as regressions. Reasoning transcripts support later analysis; they are not a direct record of all internal computation.

The actual model is **Qwen3.6-35B-A3B**, despite the older repository name `qwen3.5-9b_analysis`. The original repository's current setup already names Qwen3.6; do not substitute Qwen3.5-9B based on the repo name.

- GGUF source: `bartowski/Qwen_Qwen3.6-35B-A3B-GGUF`, revision `5c2410d71524f4f72b023ce8daf7a80528226d5f`.
- Run order: **Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M, Q2_K**.
- Engine reference: llama.cpp b11552, commit `23b0202a189c44a54625aadcb37a946dd1d6278d`.
- One pass of all 250 questions per model. Start each model separately; do not automatically chain six models.
- Use the same host/runtime/settings throughout the six-model comparison. The model file and CPU/GPU placement may vary and must be recorded. A cloud run is a new collection, not a continuation of local timing measurements.

## Exact exam and grader inputs

Use the three JSON files in this package together:

| File | Contents | Given to model? |
|---|---|---|
| exam.json | 250 questions: 200 math/logic, 50 Python coding; 50 families × 5 | Only each exact question string |
| answer_key.json | Exact final answers for 200 math/logic questions | Never |
| hidden_tests.json | 2,468 cases across 50 coding tasks | Never |

Send each question unchanged as one user message in a fresh conversation. No system prompt, history, examples, answer-key material, tools or constrained response grammar. Use the original exam file order for every quantization.

## Fixed full-study generation

The machine-readable version is core-config.json.

| Control | Value |
|---|---|
| Context | 131,072 tokens |
| Thinking | Enabled; ceiling 16,384 tokens, not a quota |
| Total generated output | 24,576 tokens INCLUDING thinking; not an additional 24,576 final-answer tokens |
| Sampling | Temperature 1.0; top-p .95; top-k 20; min-p 0 |
| Penalties | Presence 1.5; repetition 1.0; frequency 0 |
| Seed / passes | 73191 / one |
| KV / concurrent sequences | FP16 K and V / one |
| Batch / microbatch | 2,048 / 512 |
| CPU generation / prompt threads | 16 / 16 |
| Flash attention | Auto; record effective runtime behavior |
| Prompt reuse / RAM prompt cache | cache_prompt=false / cache-ram=0 |
| Speculation / automatic fitting | Disabled / off |
| Request timeout | 1,800 seconds |

Full local runner placement policy: qualify the smallest CPU-expert-layer count that fits, leaving other eligible tensors and embeddings on CUDA. Record exact placement per model. Keep at least 1,536 MiB free VRAM, 2,048 MiB host available RAM and zero model-process swap. A short load/prefill probe is not validation of a filled 128K context. Freeze any cloud-specific placement/runtime changes before collecting all six models.

## Mechanical grading and retained data

Reuse grading.py unchanged if retaining the existing scoring contract. Math is exact JSON type/key/value/list-order comparison; no float/int/bool coercion or answer repair. Report **solution correctness** and **strict response correctness** separately. A mechanically extractable correct solution can retain solution credit despite formatting failure.

Coding remains pending during inference. After all 250 generations, stop the model, then grade unchanged extracted code in serial Docker containers ONLY. All tests must pass within limits. Never execute model code on the host. Record passed/total, first failing test index/reason, CPU/wall time and peak Python RSS. Docker/harness failures are unresolved infrastructure errors, not wrong answers.

The pinned Python image and limits are in core-config.json: no network, read-only filesystem, nobody, no capabilities/new privileges, one CPU, 256 MiB RAM/no swap, 32 PIDs, 10 s CPU / 20 s wall, 16 MiB temporary filesystem. These workloads give runtime/memory diagnostics, not a calibrated LeetCode percentile or scaling study.

For every question retain the exact request, complete emitted thinking, complete final response, elapsed inference time, usage/decode rate, finish reason and separate thinking/output cutoff flags. One readable document per question starts with its mechanical grade. Canonical combined results drive all documents and scores. Checkpoint completed work; rerunning the same model resumes it. An interrupted generation must restart, with its partial attempt preserved.

Later LLM/reviewer assessment of reasoning and failure types is separate and not implemented. With the now-requested single pass, do not claim three-trial consistency measurements. Family-level conclusions have only five questions per family.

## What changed from the original repository

Baseline checked: `m-oonlight/qwen3.5-9b_analysis` at commit `e0f3d0c4dd506a079927513ab45d8674ca60c6de`.

1. **Exam cleanup:** all 250 prompt texts changed to remove redundant metadata or unused rules/fields and clarify wording. IDs, order, categories and expected answers did not change. Removed the top-level system prompt; model requests have no system message. exam-cleanup.diff records exact prompt changes.
2. **Hidden tests:** 1,233 unused input fields were removed across 1,183 cases; every retained input value and all 2,468 expected outputs are unchanged. Grading notes explicitly include 20 s wall time. changes-from-original.json gives exact hashes and counts.
3. **Answer key:** byte-identical to the original repository.
4. **Protocol:** one seed/pass instead of three seeds/trials; original file order instead of paired shuffled orders; variable qualified CPU/GPU placement instead of 30 CPU-expert layers for every quantization.
5. **Cache and integration:** RAM prompt cache explicitly disabled; the current 250-question exam and its hashes replace stale references to the older 60-question suite in systemconfig.txt.
6. **Automation:** one model-argument runner, resumability, canonical grades/documents, coding deferred until model shutdown, standalone regrading, private GitHub checkpoints every 10 minutes/finally, and quiet progress by default. Full config remains saved; --verbose prints it. These additions do not constitute a completed full study.

The local automation implementation is preserved separately under the private result repository's setup-methods/. When porting it, replace local file/build paths and omit the local telemetry dependency; do not simply run its local-machine config on an unknown server. This handoff does not select or deploy a cloud server.

## All 25 Q8 pilot results

pilot-Q8/ contains **25 readable prompt documents, 25 original JSON attempts, 25 raw SSE streams**, combined canonical results, summary, selection/order, original server command/defaults, original-config.json and launcher-exit provenance. Every prompt document includes the full question, entire emitted reasoning and entire final answer.

- **Solution correct: 21/25 (84%). Strict correct: 16/25 (64%).** Math/logic: 16/20 solution, 14/20 strict. Coding: 5/5 solution, 2/5 strict.
- Zero output truncations and zero question-level infrastructure errors. Original thinking-budget cutoff trace was unavailable; do not infer exact cutoff labels retrospectively.
- About 3 h 17 min total attempt time; mean decode 33.7 tokens/s. This was local hybrid CPU/GPU inference, not cloud performance.
- Pilot settings: Q8, seed 73191, same 128K/16K-thinking/24K-total ceilings, 30 CPU-expert layers, cache-ram=0. Exact captured settings are retained, not reconstructed from current settings.
- Original pilot coding was graded between questions, unlike the planned deferred grading protocol; subsequent isolated regrading confirmed all five passes. The launcher returned 143 after all 25 records were saved; its cause was not established.
- Pilot is excluded from the full 250-question study. No full six-model benchmark has been collected.

## File privacy and transfer

This local ZIP includes the exam, answer key and hidden tests for private transfer to the eventual server. They must stay out of model prompts. Following the earlier instruction not to upload oracle files, GitHub receives the compact handoff/config/change records and all pilot outputs; the key/test files are kept in this local transfer package. No credentials, model weights, dashboard, power logs or cloud setup are bundled.

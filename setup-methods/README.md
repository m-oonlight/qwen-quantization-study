# Qwen quantization benchmark

One command runs ONE model: load/qualify placement, infer the 250 questions, shut down the model, grade coding in serial Docker containers, finalize outputs, and upload. It never launches the next quantization automatically.

## Run

From this directory:

```bash
./benchmark.py Q8
./benchmark.py Q6
./benchmark.py Q5
./benchmark.py Q4
./benchmark.py Q3
./benchmark.py Q2
```

Run each command after the previous one finishes. The full-run order is enforced, including successful completion and upload of the previous model. A private GitHub write/push preflight must succeed before a full model is loaded. Aliases Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M and Q2_K also work. No extra input is requested by these commands after one-time setup. They can run without Codex or any agent.

Quick infrastructure test, excluded from the study:

```bash
./benchmark.py Q2 --smoke
```

This uses two unchanged exam questions (one math, one coding), seed 73191, 64 thinking tokens and 1,024 total output tokens, a three-second idle baseline, and a conservative 30-CPU-expert split. It does not qualify maximum GPU placement. Its score is NOT an accuracy benchmark. A completed smoke command is idempotent; rerunning does not generate again. To deliberately repeat it with automatic archival of the earlier smoke, run `./benchmark.py Q2 --fresh-smoke`. Omit `--fresh-smoke` when resuming an interrupted test.

Resume after a crash/power loss with the SAME model command. Completed inference is never repeated. An unfinished generation must restart because the GPU/KV state did not survive; its checkpoint is preserved in interrupted_attempts and the restart is logged. Checkpoints are written every five seconds, completed results and each grade are fsynced atomically. A lost final few seconds of an unfinished response is possible. Old server PID/start-time checks prevent killing unrelated processes. Interrupted Docker jobs are cleaned up only when labeled for this exact run.

Regrade/resume coding without loading a model:

```bash
./benchmark.py Q8 --grade-only
./benchmark.py Q8 --grade-only --regrade
```

The first continues pending/infrastructure-error grades and preserves completed ones. The second explicitly reruns coding and retains previous grades. Any active llama-server blocks grading. Never edit config/evaluator source in an existing run: resume validates the frozen fingerprint. Revised settings require a separate study/run_root; do not overwrite collected results.

## Shared configuration and placement

`config.json` is the single source of settings. Full runs use 128K context, 16,384 thinking tokens, 24,576 total output tokens, one sequence, FP16 KV cache, 16/16 threads, and the recorded sampling controls. No system prompt, history, examples, tools, grammar or response-format constraint. Original exam file order and seed 73191 are the same for every quantization. One pass only.

Only model identity and CPU/GPU expert placement vary. Initial binary-search qualification finds the minimum CPU-expert-layer count that passes the shared allocation/prefill probe with at least 1,536 MiB free VRAM and zero model-process swap. Other layers and embeddings stay on GPU; automatic fitting is disabled. Every placement trial, exact command, loaded server defaults, source/model/runtime hashes and hardware details are recorded. This qualifies the probe, not a filled 128K context. The same guard runs during actual inference and stops the run on violation. The model process runs in its own session/process group so shutdown cannot signal the runner's process group.

The full effective configuration is saved in configuration.json at each invocation and again after placement/loaded-default resolution. Default terminal output is a short config-path notice, one updating progress line (Idle/Load/Fit/Infer/Grade/Upload), and the final score. Use `--verbose` to also print the full configuration. Redirected output records only phase/count changes rather than one new line per second. `C-PEND` is the number of coding grades pending. Tokenizer metadata was compared across all six supplied GGUFs and matched; each loaded chat template must match the shared reference. Engine/model/library hashes are checked on every load/resume.

## Mechanical grading

Primary score is **solution correctness**; strict response format is a separate column. Exact math JSON types/keys/values/list order must match the answer key, with no float/int/bool coercion or fraction repair. Missing markers or JSON fences can lose strict credit while a mechanically extractable exact answer retains solution credit. Extraction rules are implemented in grading.py and fixed before collection. Only final response content is scored, never the reasoning transcript.

Coding stays PENDING throughout all 250 inference requests. After the model exits, unchanged fenced solve(data) source is policy-checked and run in one pinned Docker container at a time: no network, read-only filesystem, nobody, no capabilities/new privileges, 256 MiB RAM/no swap, one CPU, 32 PIDs, 10-second CPU/20-second wall limits, 16 MiB tmp. All tests must pass and input must compare unchanged. First failing test is recorded by index and reason; hidden inputs/expected outputs are never exported. No repair or LLM grading. Docker launch/daemon/harness failures are infrastructure errors, not wrong answers; the final score is incomplete until they are resolved.

Emitted reasoning/final text, exact requests, finish reasons, usage, inference wall time, first-token latency and server decode rate are retained. Thinking cutoff comes from the engine's budget-exhaustion/natural-end trace, not retokenized text or a token-count guess. Missing trace means unknown. Output truncation is finish_reason=length. Neither flag automatically changes the primary solution score; strict format requires a complete response.

Generated-code CPU/wall time and peak container Python RSS are recorded as diagnostics. These small hidden-test workloads are not a standalone algorithmic-complexity/LeetCode efficiency study. No future LLM assessment or reasoning-quality score is implemented.

## Outputs and backups

Each full model has a local `runs/QUANT/` folder containing 250 Markdown prompt documents plus nine data/log/config files (259 total):

- prompts/001-QUESTION.md through prompts/250-QUESTION.md: grade at top, exact prompt, entire emitted thinking, entire final answer; coding documents update after grading.
- results.json: canonical source for every score and document, including interruptions, timing, energy and previous coding grades.
- summary.json: final score out of 250 only when all grades are resolved; separate pending/infra/strict/truncation counts.
- configuration.json: shared config, effective command/defaults, model/placement, hashes and system details.
- energy.json: per-prompt, whole-run, per-phase, baseline and above-idle energy.
- stress.jsonl: one-second RAM/RSS/PSS/swap, VRAM, CPU/GPU utilization, temperatures, CPU/GPU clocks, GPU throttle reason bitmask, exposed CPU throttle counters, power/counter readings.
- diagnostics.jsonl, runtime.log, recovery.json, upload.json: auditable failures, engine trace, durable in-flight checkpoint, and upload status.

results.json is authoritative; every prompt document and summary is regenerated from it. Final document headings are checked against the canonical grades. Once all six summaries are complete, the command prints a comparison table and writes runs/comparison.json.

GitHub commits/pushes allowlisted snapshots to the private repository **https://github.com/m-oonlight/qwen-quantization-study**. Periodic backups run every 600 seconds and after completion/interruption. Snapshots derive documents and summary from the same canonical results. A verified remote commit SHA is recorded locally. Failed pushes preserve their local commits for retry; no force pushes or history rewrites. A full run must successfully write/push before loading its model. The runner checks that the destination remains private and writable on each upload.

Question documents and results remain plain Markdown/JSON. Remote stress/runtime/diagnostic logs are split into 8 MiB byte chunks with an ordered checksum manifest. Restore their exact original bytes with github_backup.py; local logs stay in their normal format. This adds manifest/chunk files to the remote folder in place of the three raw logs; the local full-model layout remains 259 files. Other artifacts at or above 90 MiB are refused before commit. The final six-model comparison is published at repository root once all six are complete.

Answer keys, hidden tests, GGUFs, sudo credentials, GitHub tokens and rclone config are excluded. The GitHub credential helper uses the one-time saved local authentication without browser/agent involvement. Upload failures remain visible, return a nonzero status and leave local results intact. Rerunning a completed command retries backup without repeating inference/grading. See BACKUP-SETUP.md for authentication, restoration and recovery. Google Drive is no longer used.


## Electricity

CPU-package energy uses accumulated Linux powercap energy_uj, wrap-corrected at one-second intervals; package counters only, so nested core domains are not double-counted. GPU energy integrates NVIDIA driver watts by the trapezoid rule. Their combined kWh is **CPU package plus GPU device**, not wall electricity (RAM, storage, fans and PSU losses are not measured). No CPU power estimates are substituted.

A short idle baseline is measured before model load on every invocation; baseline and execution segments are retained on resume. Above-idle values are signed differences and may be slightly negative from noise. Whole-run totals are reconstructed from fsynced telemetry, including incomplete attempts; no electricity during powered-off gaps is invented. Counter/telemetry failures are recorded and coverage should be checked. Other system activity is included in package/device readings.

Read access to CPU energy counters was enabled for group cs4 and a udev rule installed for future boots. If a kernel/device change breaks it, rerun `sudo ./enable-cpu-energy.sh` and retry the same model command. Unsupported CPU throttle counters are null, not claims of no throttling.

The historical pilot predates exact CPU counter measurements and thinking-budget tracing. Missing pilot measurements remain unavailable; old CPU/system power estimates are not represented as measured CPU energy. It also graded coding during the original inference session, unlike this new full-run protocol. The pilot remains excluded from the full study.

## CPU-only tests

```bash
python3 -m unittest -v test_benchmark test_github_backup
RUN_DOCKER_TESTS=1 python3 -m unittest -v test_benchmark test_github_backup
```

Neither command loads a model or uses the GPU. Offline Git tests additionally use temporary bare repositories to verify chunk restoration, privacy checks, unchanged snapshots, and interrupted-push retries. No GitHub login is needed for those tests. The second command also executes synthetic code in CPU-only Docker containers to verify success/failure counts, first failure, mutation, exact types and limits. No actual exam key/tests are bundled into the test fixtures.

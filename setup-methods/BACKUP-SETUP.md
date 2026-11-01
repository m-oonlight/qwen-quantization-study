# Unattended private GitHub backups

Destination: https://github.com/m-oonlight/qwen-quantization-study (PRIVATE).

The GitHub CLI has been authorized once and stores credentials in the system keyring. The runner calls the installed `gh` Git credential helper with prompting disabled. No agent or signed-in browser session is required during a run. Use the same Linux user account and keep its credential store accessible. A revoked credential or unavailable keyring produces an explicit backup error rather than a login prompt inside inference.

Each command performs a real private-repository write/verified-push check before a full model loads. The repository must remain private and writable; every backup checks this. The six model commands remain separate and keep the same scientific configuration. The Google Drive/rclone destination is superseded; no Google Cloud setup is needed.

## What is published

- `setup-methods/`: allowlisted scripts, shared config, hardware/model inventory, protocol, tests and validation.
- `runs/pilot-Q8/`: historical 25-question pilot, labeled excluded from the full study.
- `runs/smoke-Q2_K/`: two-question infrastructure test with deliberately small budgets, excluded from accuracy analysis.
- `runs/Q8_0/`, `runs/Q6_K/`, `runs/Q5_K_M/`, `runs/Q4_K_M/`, `runs/Q3_K_M/`, `runs/Q2_K/`: each added by its own command.
- `comparison.json`: added once all six full model results are complete.

Only an explicit file allowlist is exported. No actual answer key, hidden tests, model weights, sudo password, GitHub credentials or rclone config is included. Paths and hashes naming private local datasets are retained as reproducibility metadata; their contents are not copied. The old pre-GitHub tools/smoke remain archived locally and are not mixed into the current smoke or study.

## Periodic and final delivery

A canonical snapshot is committed/pushed every 600 seconds, after completion and after an interruption when possible. Completed prompts and grades are fsynced locally independently of Git. Each remote snapshot regenerates its question documents and summary from the same results.json. Unchanged snapshots produce no new commit. Failed pushes retain their local commits and are retried, without force-pushing or rewriting history. The verified remote commit SHA is recorded in the local run's upload.json. The remote upload.json explains that its enclosing Git commit is the snapshot's publication record.

The private local checkout at `github-repository/` contains only sanitized snapshots. It is deliberately separate from the exam files and working tree. Do not manually edit this checkout during a run. After a lost disk, cloning the repository restores the public artifacts; rerunning inference also requires the original private datasets and matching model/runtime files. Merely copying saved results to a new directory does not claim that a GPU generation can continue mid-token.

## Stress/runtime logs and restoration

Local stress.jsonl, diagnostics.jsonl and runtime.log remain normal files. Remote copies use 8 MiB byte chunks under each run's `logs/`, plus `logs-manifest.json` with ordered paths, byte lengths and SHA-256 hashes. A chunk can split a JSON line; concatenate all parts before parsing. This retains the complete original bytes and avoids GitHub's per-file limit. Files at or above 90 MiB outside the chunked logs are refused before commit, with an explicit error.

To restore exact logs after cloning:

```bash
python3 setup-methods/github_backup.py --restore-logs runs/Q8_0 --destination restored/Q8_0
```

Other artifacts, including the canonical results.json, remain directly readable. GitHub retains previous snapshots in commit history. This is research artifact versioning, not a promise of unlimited storage.

## Credentials and recovery

To verify the saved login:

```bash
gh auth status
```

If access is revoked, use `gh auth login --hostname github.com --git-protocol https --web` once outside a benchmark run. Never paste the resulting token into config.json or results. The runner requires no repeated browser authorization after a valid saved login.

To retry a completed model's upload, rerun its exact command; completed inference and grading are not repeated. A nonzero exit code 3 means local inference/grading completed but backup failed. After a partial run, the same command resumes the remaining questions and pending grading.

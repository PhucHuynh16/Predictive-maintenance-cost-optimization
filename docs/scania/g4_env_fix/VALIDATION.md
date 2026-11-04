# ENV fix implementation and validation — 2026-11-05

Implemented under [owner authorization #6600384968](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-6600384968). Source commit **`9cf8ab660f2d9bd79cbef524c1e0a16232a2eef8`**, parent/main `d78cfcd30601090211003ef3a6a6751f83dd6eb3`; branch `codex/sc-g4-b1-env-fix`. The accepted B1 branch/PR #16 remains separate at `ec837901729b40949345b917076e6a0fd4870d09`.

Source digest for the adapter, runner and test file: **`65769791cd1fccefb76112b934edd2292b80d442d1a12f3e2ac0c30a5df442c0`**. Digest semantics: SHA-256 of sorted compact UTF-8 JSON mapping relative source paths to canonical-LF SHA-256, followed by LF. Source/config/versions were captured before bound pytest/native execution and checked after it. Documentation is outside this three-file code digest.

## Results on committed source

[Bound tests](../../../results/scania_aps/g4/env_fix/bound_tests_20261105_01/tests_summary.json): **109 PASS, 0 FAIL/ERROR/SKIP**, total subprocess wall **8.8603784s**. **69 ENV cases across ENV01–ENV24 + 40 G3 cases G301–G310**. The [source manifest](../../../results/scania_aps/g4/env_fix/bound_tests_20261105_01/source_manifest.json) identifies the actual commit above. Environment/protected/source postchecks all passed. This is not a rerun of the separate Gate A/B1 174-case suite.

Coverage includes Unicode/ASCII fixtures; corrupt/empty/truncated snapshot text and bounded Wide fallback; snapshot/PSAPI/API errors; handle/path/hash/race mismatch; unknown/duplicate/missing runtimes; consumer extensions versus exported runtime APIs; controller coverage/identity; null/bool/noninteger/>1 thread limits; process pre-import evidence and main-thread/context restrictions; late numerical/foreign-native imports and ctypes loads; warning-as-error; no-fit AST checks; data/output guards; failure finalization; collision preservation; source changes; cleanup/close/I/O errors; missing/extra/tampered/CRLF/alias evidence; direct worker handshake and rejecting fixture-only proof as native PASS.

The six native runs below all use committed source `9cf8ab6`, the existing locked Python environment and a Windows Job Object. Every started worker has **job-empty verified**, unchanged source/protected snapshots, no real fit or Validation scoring.

| Run ID prefix `native_bound_` | Actual status / CLI exit | Total supervisor seconds | Actual evidence |
|---|---|---:|---|
| `normal_01` | PASS / 0 | 4.1087821 | Full three-pool reconciliation and 7 checkpoints; all three synthetic oracles pass |
| `normal_02` | PASS / 0 | 4.7764403 | Exact same worker-result bytes and stable digest as normal01 |
| `crash_01` | FAILED / 2 | 1.0373897 | Intentional worker exit37, absent worker result, supervisor diagnostics saved |
| `timeout_01` | FAILED / 2 | 1.7692418 | Worker journal reached intentional sleep; fixed 1s launch deadline terminated the job; absent worker result |
| `late_import_01` | BLOCKED / 2 | 3.6608258 | `LATE_NUMERIC_IMPORT`, limiter restored/context closed, failure evidence retained |
| `data_guard_01` | BLOCKED / 2 | 3.7923734 | Nonexistent Test-named sentinel blocked before open, limiter restored/context closed |

Total supervisor time includes preflight, postcheck and cleanup, and is **not** a separately measured worker-only duration. Fixed timeout/profile limits are diagnostic values; they do not approve production RAM, runtime, CPU policy or official/reproduction budget.

Both normal runs have stable digest **`f6009cb4825aa529b13da1087bbc8a7b0df60315a3b5b5c295b7d07e61c2df8d`**. Native worker-result documents are exactly equal. This demonstrates same-host synthetic/native reproduction, not real baseline reproducibility or fresh-environment/cross-OS portability.

## What native PASS establishes

For the diagnosed stack, Wide paths resolve actual loaded modules even when snapshot text differs. All controller handles, library hashes, APIs and runtime inventories reconcile. Two OpenBLAS pools (`0.3.30` SciPy / `0.3.31.188.0` NumPy) and vcomp OpenMP report integer **1** at every ordered checkpoint: before, during entry, after NumPy, after SciPy, after the OpenMP workload, during exit, after restore. Built-in OpenMP controller version is null because that API does not report it; its DLL hash is pinned. Its **num_threads is 1**, not null.

Numerical work is fabricated: NumPy dot sum8, SciPy dgemm sum8, compiled OpenMP sparse-L1 distance sum6 for two fabricated CSR rows. All numerical imports occur after the fresh-worker one-thread environment check. No estimator is instantiated/fit or used for prediction/scoring. Getters/context checkpoints do not measure continuously scheduled OS thread counts and are not a security guarantee for arbitrary native callbacks.

Environment is Python **3.11.9**, Windows x64/kernel **10.0.26100**. All 15 package versions match the unchanged `configs/scania/g3_pipeline.json` environment / `g3_requirements.lock.txt`: NumPy2.4.6, SciPy1.17.1, sklearn1.9.1, threadpoolctl3.7.0, joblib1.6.0 and the recorded transitive/test dependencies. NativeSession measures/compares the installed threadpoolctl source against pinned SHA-256 `e5f119e394193e206655bec4b993ef0bb40b0fbb2f22c92bd5b2d70a622bb518` before constructing controllers. The runner's environment metadata field of that name stores the **expected contract hash**; independently measured source/DLL hashes are in [final preservation](../../../results/scania_aps/g4/env_fix/delivery_20261105_01/final_preservation.json).

## Preserved failed and intermediate attempts

All native attempts remain under the new ENV namespace. The [index](../../../results/scania_aps/g4/env_fix/delivery_20261105_01/native_and_test_index.json) distinguishes each source digest/commit and whether it matches the final source; historical PASS is not assigned to later code. **12 native attempt records / 118 native checksum entries** were verified, including early BLOCKED attempts and intentional failures.

- `native_initial_01` and `native_diagnostic_02`: an overbroad name hint initially classified `_fblas.pyd` as a runtime. The final classifier distinguishes a consumer `.pyd` without runtime exports; an exporting/unknown native module still blocks. Positive/negative fixtures cover both cases.
- `native_initial_03`: ArgKmin requested sklearn's stock nested threadpool collector, triggering `LATE_CTYPES_LIBRARY_LOAD`. No dependency/cache was patched and the guard was not relaxed. The final workload uses the compiled `_sparse_manhattan` OpenMP kernel directly. This is an important **integration limitation**, not proof that every sklearn helper now works.
- `native_initial_04` and `native_precommit_05`: intermediate working-tree native PASS; not final-source acceptance proof. `native_precommit_06` and `precommit_tests_06` match the final three-file digest, with pre-execution working-tree binding. The committed-source runs above are the final proof.
- Initial pytest attempt could not save a complete JUnit because sandbox writes to the newly registered worktree were denied; no final PASS is claimed. Historical raw XMLs include 52-pass, 107-pass and 108-pass intermediate suites. An earlier suite had **41 passed / 12 error events** (11 errored cases; setup and teardown errors can belong to the same case), caused by a 32K fixture parameter becoming an overlong Windows environment value and missing fixture-parent preparation. Parameter display IDs/directory preparation were fixed without changing oracles. The [history](../../../results/scania_aps/g4/env_fix/delivery_20261105_01/test_history.json) and counter clarification retain that history.

Raw JUnit/terminal traces and pytest fixtures stay local under `env_fix/local_only/`, excluded from publication. Historical unbound XMLs have hashes/status summaries but no invented pre-run source binding; their intermediate source bytes were not archived separately. A checksum proves byte integrity, not independently that a test was executed. Owner-assigned independent review remains necessary.

## Preservation and publication scope

The [final audit](../../../results/scania_aps/g4/env_fix/delivery_20261105_01/final_preservation.json) verifies:

- **173 files** from main/G3 unchanged in the new worktree, digest `2ab50db89e91548ca4f6e903894232c71aa9ab0478972a5ccb505fe47f8a1f63`.
- The original B1 checkout still at `ec83790`, **618 tracked files unchanged**, digest `6e794f73f6564443c55782d2ac123fba1b772bf0e3b8f3b125521678aa0ffb24`; six private original files unchanged and not copied/published.
- Nine selected existing environment files (venv config, threadpoolctl/NumPy/SciPy startup source and native DLLs) retain their measured hashes. This is not a hash audit of every site-packages file.
- No real Train/Validation/Test data was opened/rehashed/generated. No raw/processed data, membership, preprocessing, G3 artifact or accepted Gate A/B1 file was edited. No installed package, DLL, OS/PATH/registry/locale or PR #16 was changed.

Public evidence is selected by exact file paths and scanned before staging; no recursive `git add` of the ENV directory or local-only logs. Native evidence verifies canonical-LF hashes. Test/delivery raw hashes refer to the committed LF blob bytes; a CRLF checkout must not silently reinterpret those as raw-byte checksums. The final delivery inventory records this distinction and the exact public paths/hashes.

## Handoff

The standalone adapter/native qualification is ready for **owner-assigned independent ENV fix review**. It is not integrated into accepted B1, sklearn's global collector/cache, or a B2 execution path. Such integration requires separate owner scope; the exploratory nested-collector failure above is retained to make that boundary reviewable. No claim is made that an estimator workload, production cap300s/minimumRAM4GiB, fresh installation, other host/OS, convergence or real baseline result has been verified.

**ENV FIX: IMPLEMENTED AND TESTED — INDEPENDENT REVIEW / OWNER ACCEPTANCE PENDING.**

**GATE B2: NOT AUTHORIZED. OFFICIAL TEST: SEALED UNTIL G10. PR #16: KEEP DRAFT / DO NOT MERGE.**

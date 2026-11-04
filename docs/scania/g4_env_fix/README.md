# SC-G4-B1-ENV standalone discovery adapter

Owner authorization: [Issue #17, comment 6600384968](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-6600384968), 2026-11-03 (Asia/Saigon). Diagnosis: [6600253425](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-6600253425). This branch starts at main/G3 `d78cfcd30601090211003ef3a6a6751f83dd6eb3`. It adds three independent implementation/test/runner files plus new ENV documentation/evidence. It does not integrate into the accepted B1 worker or change PR #16.

## Behavior

On the diagnosed Windows host, Toolhelp snapshot text loses two Unicode characters, although `GetModuleFileNameW` resolves the correct existing file for the same handle. The adapter uses snapshot **handles**, always resolves each handle through bounded Wide APIs, and reconciles handles against independent PSAPI enumeration. Empty/truncated snapshot *text* is harmless only if Wide resolution and all remaining checks succeed; missing snapshot handles/API failures are blocking. No guessed string repair or global monkey-patch is used.

Candidates are identified by native DLL naming or supported runtime exports. A `.pyd` consuming BLAS, such as `_fblas`, is not treated as a pool merely because its filename contains `blas`; if it exports a runtime API it is still classified and an unknown runtime blocks. Every expected runtime must have the correct path/loaded handle, pinned DLL SHA-256 and built-in controller. Unknown, missing, duplicate or unaccounted runtimes fail closed. The supported scope is the locked Windows x64 NumPy/SciPy/sklearn stack, not arbitrary numerical runtimes or operating systems.

The adapter pins `threadpoolctl==3.7.0` and its installed source hash. A local subclass changes only its collector, retaining threadpoolctl's built-in controllers and limiter context. It requires pre-import env evidence from the same fresh process, the main Python thread, exactly one active context, and integer `num_threads==1` at ordered before/during/after checkpoints. Late numerical imports or ctypes library loads during the context block; changed module inventory, files, environment, warning/partial discovery or invalid controller coverage block. It leaves installed packages, ctypes and stock library controllers unchanged.

## Native qualification

The standalone worker sets one-thread env before numerical imports. Inside the verified context it executes fabricated arrays only:

- NumPy `dot` on two 2x2 all-one matrices: sum **8**.
- SciPy BLAS `dgemm` on the same fabricated matrices: sum **8**.
- sklearn's compiled `_sparse_manhattan` OpenMP `prange` kernel on the fabricated CSR rows `[1,0]` and `[0,2]`: distance matrix `[[0,3],[3,0]]`, sum **6**; compiled OpenMP support must be true.

All three loaded pools (two different OpenBLAS DLLs and vcomp OpenMP) are reconciled before entry, on entry, after each workload, before exit and after restoring the built-in limiter. Getters report configured limits, not a measurement of the number of OS threads continuously scheduled. The fixed trusted diagnostic workload contains no intervening thread-limit mutations; this is not an OS sandbox for arbitrary callbacks.

Supervisor creates the worker suspended, queries/verifies a Windows Job Object before resume, denies breakaway, uses kill-on-close, limits active processes to 2 (venv shim plus worker), and caps committed job memory at 512 MiB. Qualification has a 20-second absolute launch-to-exit deadline; the explicit timeout scenario uses 1 second and sleeps before numerical imports so the timeout reaches the intended blocking stage. Cleanup has a separate 5-second grace and verifies zero active processes. These are diagnostic limits, not approved production values. It records failed/blocked attempts and finalizes diagnostics/checksums even when the worker crashes or cannot start. Disk/handle failures do not become PASS. Whole-machine/kernel/disk failures cannot guarantee completion of final JSON.

Worker admission uses an exclusive claim and per-attempt nonce hash. No external dataset/permit/config/threshold/model options exist. Software I/O guards reject data/archive paths and out-of-run writes; negative data tests use nonexistent sentinel names, never official Test. No B1/B2 fitting, prediction, Validation scoring or optimizer is exposed.

## Reproduction commands

Use the existing owner-approved Python 3.11.9 environment with the unchanged G3 dependency lock. In a new worktree, set the local PowerShell variable `$diagPython` to that executable; the task does not create or install another venv. Commands below are synthetic/native diagnostics only. Choose unused run IDs.

```powershell
& $diagPython -B -X utf8 -m pytest tests/scania/test_g4_env_discovery.py tests/scania/test_pipeline.py -q -p no:cacheprovider
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_normal_01 --scenario normal
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_normal_02 --scenario normal
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_crash_01 --scenario crash
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_timeout_01 --scenario timeout
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_late_import_01 --scenario late_import
& $diagPython -B -X utf8 scripts/diagnose_scania_native_pools.py qualify --run-id review_data_guard_01 --scenario data_guard
```

Normal runs should pass only with full native proof. Crash/timeout should fail and preserve supervisor evidence; late import/data guards should block. Evidence status is distinct from checksum integrity: a valid failed-run checksum set is not a passing qualification. Runtime evidence uses canonical LF hashes, preserving compatibility with Git CRLF checkout; raw capture hashes, when present in delivery/test records, are explicitly separate.

## Important integration limit

The global `threadpoolctl.threadpool_info()` remains unchanged. Nested sklearn helpers that instantiate a stock cached collector can still hit the original discovery problem. An exploratory ArgKmin workload did exactly that and was blocked by the late-load guard; its failed evidence is retained. No sklearn cache/dependency is monkey-patched. The final synthetic OpenMP workload calls a compiled kernel directly to exercise OpenMP under this standalone verified context.

Therefore standalone native qualification does **not** establish that every estimator/sklearn helper or the accepted B1/B2 execution path is integrated. That integration, production workload/convergence/RAM/runtime/budget and any environment changes need separate owner scope/approval. The accepted B1 source and its historical evidence stay unchanged; tests on this branch cover ENV plus G3 fixtures, not a new claim to have rerun Gate A/B1's entire 174-case suite.

Gate B1 is accepted in infrastructure/synthetic safety scope only. ENV fix acceptance and Antigravity independent review remain pending. **Gate B2 is NOT AUTHORIZED; official Test is SEALED UNTIL G10. Do not merge either PR or open real execution automatically.**

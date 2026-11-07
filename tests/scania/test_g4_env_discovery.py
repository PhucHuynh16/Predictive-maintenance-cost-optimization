"""ENV fixtures: no numerical imports, real data or accepted artifact writes."""
import ast
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import warnings

import pytest
from src.scania import g4_env_discovery as e

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("env_runner", ROOT / "scripts/diagnose_scania_native_pools.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
NAMES = list(e.RUNTIMES)


class Backend:
    """Explicitly synthetic DLL/handle/hash data, never loads a fixture DLL."""
    def __init__(self):
        self.paths = {i + 1: str(ROOT / "fixture_Unicode_ậố" / n) for i, n in enumerate(NAMES)}
        self.snap = [(h, p.replace("ậ", "?").replace("ố", "?")) for h, p in self.paths.items()]
        self.independent = list(self.paths)
        self.loaded = {p: h for h, p in self.paths.items()}
        self.hashes = {p: e.RUNTIMES[Path(p).name][0] for p in self.paths.values()}
        self.missing = set()
    def snapshot(self): return list(self.snap)
    def handles(self): return list(self.independent)
    def resolve(self, h): return self.paths[h]
    def loaded_handle(self, p): return self.loaded.get(p)
    def file_hash(self, p): return self.hashes[p]
    def exists(self, p): return p not in self.missing
    def has_symbol(self, h, s): return s == "runtime_get_threads"


class Limiter:
    def __init__(self, owner): self.owner = owner; self.owner.limit_calls += 1
    def __enter__(self): return self
    def __exit__(self, *args): self.owner.restores += 1


class Controller:
    backend = None
    bad = None
    def __init__(self):
        self.lib_controllers = []; self.limit_calls = 0; self.restores = 0
        self._load_libraries()
    def _make_controller_from_path(self, path):
        self.lib_controllers.append(SimpleNamespace(path=path,
            dynlib=SimpleNamespace(_handle=self.backend.loaded_handle(path))))
    def info(self):
        result = []
        for c in self.lib_controllers:
            expected = e.RUNTIMES[Path(c.path).name]
            result.append(dict(filepath=c.path, user_api=expected[1], internal_api=expected[2],
                               num_threads=1, version="fixture", threading_layer="fixture"))
        if self.bad:
            self.bad(result)
        return result
    def limit(self, *, limits):
        assert limits == 1
        return Limiter(self)


@pytest.fixture
def fixture_session(monkeypatch):
    b = Backend()
    monkeypatch.setattr(Controller, "backend", b)
    monkeypatch.setattr(Controller, "bad", None)
    monkeypatch.setattr(e, "_PREPARED_PID", os.getpid())
    monkeypatch.setattr(e, "_ACTIVE", None)
    for k, v in e.THREAD_ENV.items(): monkeypatch.setenv(k, v)
    tp = SimpleNamespace(ThreadpoolController=Controller,
        _ALL_CONTROLLERS=[SimpleNamespace(check_symbols=("runtime_get_threads",))])
    return b, tp


def session(fixture):
    b, tp = fixture
    return e.NativeSession(_backend=b, _threadpoolctl=tp)


@pytest.mark.parametrize("snapshot_text", ["", "?" * 259, "wrong_ascii_path", "truncated"])
def test_ENV01_snapshot_text_never_used_as_authoritative_path(snapshot_text):
    b = Backend(); b.snap = [(h, snapshot_text) for h in b.paths]
    rows = e.collect(b, ["runtime_get_threads"])
    assert len(rows) == 3 and all("ậố" in r.path and not r.snapshot_matches_wide for r in rows)


def test_ENV01_ascii_paths_and_symbols_reconcile():
    b = Backend(); b.paths = {h: p.replace("ậố", "ascii") for h, p in b.paths.items()}
    b.snap = list(b.paths.items()); b.loaded = {p:h for h,p in b.paths.items()}
    b.hashes = {p:e.RUNTIMES[Path(p).name][0] for p in b.paths.values()}
    assert all(r.snapshot_matches_wide for r in e.collect(b, ["runtime_get_threads"]))


def test_ENV02_wide_truncation_grows_and_api_failure_uses_bounded_fallback():
    calls = []
    def w(h, size): calls.append(size); return (size, "x" * size)
    assert e.bounded_wide_path(1, w, lambda h, n:(4,"wide")) == "wide"
    assert calls == [260,32768]
    assert e.bounded_wide_path(1, lambda h,n:(0,""), lambda h,n:(4,"wide")) == "wide"


@pytest.mark.parametrize("n,value", [(0,""),(32768,"x"*32768),(5,"wide")], ids=['empty','truncated','wrong_length'])
def test_ENV02_unresolved_or_truncated_path_is_blocked(n,value):
    with pytest.raises(e.NativeBlocked):
        e.bounded_wide_path(1, lambda h,s:(0,""), lambda h,s:(n,value))


@pytest.mark.parametrize("kind", ["empty","duplicate","race","invalid_handle","missing_path","path_handle","hash","unknown","missing_runtime","duplicate_path","symbols","question_path"])
def test_ENV03_inventory_errors_never_pass(kind):
    b=Backend(); p=b.paths[1]
    if kind=="empty": b.snap=[]
    elif kind=="duplicate": b.snap.append(b.snap[0])
    elif kind=="race": b.independent.append(99)
    elif kind=="invalid_handle": b.snap[0]=(True,p)
    elif kind=="missing_path": b.missing.add(p)
    elif kind=="path_handle": b.loaded[p]=99
    elif kind=="hash": b.hashes[p]="0"*64
    elif kind=="unknown":
        b.paths[1]=str(ROOT/"fixture/unknown_compute.dll"); b.snap[0]=(1,b.paths[1])
    elif kind=="missing_runtime": b.snap=b.snap[1:]; b.independent=b.independent[1:]
    elif kind=="duplicate_path": b.paths[2]=p
    elif kind=="symbols": b.has_symbol=lambda *args:False
    elif kind=="question_path": b.paths[1]=p.replace("ậ","?")
    with pytest.raises(e.NativeBlocked): e.collect(b,["runtime_get_threads"])


def test_ENV03_module_changes_during_hash_is_blocked():
    b=Backend(); original=b.file_hash
    def mutate(p):
        answer=original(p); b.paths[1]=str(ROOT/"changed.dll"); return answer
    b.file_hash=mutate
    with pytest.raises(e.NativeBlocked,match="MODULE_CHANGED"):
        e.collect(b,["runtime_get_threads"])


@pytest.mark.parametrize('exported',[False,True])
def test_ENV03_blas_consumer_extension_is_not_silently_a_runtime(exported):
    b=Backend(); b.paths[4]=str(ROOT/'fixture/_fblas.cp311-win_amd64.pyd')
    b.snap.append((4,b.paths[4])); b.independent.append(4)
    b.has_symbol=lambda h,s:h<=3 or exported
    if exported:
        with pytest.raises(e.NativeBlocked,match='UNKNOWN_NATIVE_RUNTIME'):
            e.collect(b,['runtime_get_threads'])
    else:
        assert len(e.collect(b,['runtime_get_threads']))==3


def test_ENV04_controller_context_before_during_after_and_restore(fixture_session):
    s=session(fixture_session)
    with s:
        s.checkpoint("synthetic_compute")
        assert e._ACTIVE is s
    assert s.controller.limit_calls==1 and s.controller.restores==1
    assert [p['stage'] for p in s.checkpoints]==['before','during_enter','synthetic_compute','during_exit','after_restore']
    assert s.public()['kind']=='SYNTHETIC_FIXTURE' and s.closed and e._ACTIVE is None
    assert all(len(c['pools'])==3 and all(p['num_threads']==1 for p in c['pools']) for c in s.checkpoints)
    with pytest.raises(e.NativeBlocked): s.__enter__()


@pytest.mark.parametrize("bad", [None, True, False, 0, 2, 1.0])
def test_ENV05_null_bool_noninteger_or_multiple_threads_blocked(fixture_session,monkeypatch,bad):
    monkeypatch.setattr(Controller,'bad',staticmethod(lambda rows:rows[0].update(num_threads=bad)))
    with pytest.raises(e.NativeBlocked,match='THREADS_NOT_ONE'): session(fixture_session)


@pytest.mark.parametrize('kind',['missing','duplicate','api','handle','version','path'])
def test_ENV06_controller_coverage_identity_and_api(fixture_session,monkeypatch,kind):
    def corrupt(rows):
        if kind=='missing': rows.pop()
        elif kind=='duplicate': rows[1]['filepath']=rows[0]['filepath']
        elif kind=='api': rows[0]['user_api']='unknown'
        elif kind=='version': rows[0]['version']=None
        elif kind=='path': rows[0]['filepath']=str(ROOT/'unrelated.dll')
    if kind=='handle':
        original=Controller._make_controller_from_path
        def make(self,p): original(self,p); self.lib_controllers[-1].dynlib._handle=99
        monkeypatch.setattr(Controller,'_make_controller_from_path',make)
    else: monkeypatch.setattr(Controller,'bad',staticmethod(corrupt))
    with pytest.raises(e.NativeBlocked): session(fixture_session)


def test_ENV07_import_evidence_and_env_are_required(monkeypatch,fixture_session):
    with pytest.raises(e.NativeBlocked): e.check_import_contract({'numpy'},e.THREAD_ENV)
    with pytest.raises(e.NativeBlocked): e.check_import_contract({},dict(e.THREAD_ENV,OMP_NUM_THREADS='2'))
    monkeypatch.setattr(e,'_PREPARED_PID',None)
    with pytest.raises(e.NativeBlocked,match='PREIMPORT'): session(fixture_session)


@pytest.mark.parametrize('event,args', [('import',('numpy._ENV_MISSING_SENTINEL',)),
    ('import',('foreign_fixture','foreign_fixture.pyd')),('ctypes.dlopen',('unknown.dll',))])
def test_ENV08_late_import_and_load_blocked_and_context_restored(fixture_session,event,args):
    s=session(fixture_session)
    with pytest.raises(e.NativeBlocked):
        with s: e._import_guard(event,args)
    assert s.closed and s.controller.restores==1 and e._ACTIVE is None


def test_ENV08_late_inventory_and_thread_drift_fail_on_exit(fixture_session):
    s=session(fixture_session)
    with pytest.raises(e.NativeBlocked):
        with s: fixture_session[0].independent.append(99)
    assert s.closed and s.controller.restores==1


def test_ENV09_warning_is_not_silent_partial_success(fixture_session,monkeypatch):
    def warn(self,path): warnings.warn('fixture discovery warning',RuntimeWarning)
    monkeypatch.setattr(Controller,'_make_controller_from_path',warn)
    with pytest.raises(RuntimeWarning): session(fixture_session)


def test_ENV10_no_fit_or_scoring_calls_and_stdlib_adapter():
    for name in runner.SOURCES[:2]:
        tree=ast.parse((ROOT/name).read_text('utf-8'))
        assert not any(isinstance(n,ast.Attribute) and n.attr in {'fit','fit_transform','predict','predict_proba','score'} for n in ast.walk(tree))
    tree=ast.parse((ROOT/runner.SOURCES[0]).read_text('utf-8'))
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(k in ast.unparse(n) for k in ('numpy','sklearn','scipy')) for n in tree.body)


@pytest.mark.parametrize('name',['aps_failure_test_SENTINEL.txt','sentinel.csv','sentinel.npy','sentinel.npz','archive.zip'])
def test_ENV11_data_guard_before_open(tmp_path,monkeypatch,name):
    hooks=[]; monkeypatch.setattr(runner.sys,'addaudithook',hooks.append)
    runner.install_io_guard(tmp_path)
    with pytest.raises(e.NativeBlocked,match='DATA_ACCESS'):
        hooks[0]('open',(str(tmp_path/name),'rb',os.O_RDONLY))
    with pytest.raises(e.NativeBlocked,match='WRITE_OUTSIDE'):
        hooks[0]('open',(str(tmp_path.parent/'outside.txt'),'w',os.O_CREAT|os.O_WRONLY))


class FakeJob:
    def __init__(self,argv,variables):
        self.run_id=argv[argv.index('--run-id')+1]
        self.scenario=argv[argv.index('--scenario')+1]
        self.limits={'fixture':True}; self.closed=False
    def resume(self):
        if self.scenario=='late_import':
            runner.write_json(runner.output_path(self.run_id)/'worker_result.json',dict(scenario=self.scenario,status='BLOCKED',native_verification='NOT_VERIFIED',
                real_estimator_fits=0,validation_scored=False,b2_authorized=False,official_test='SEALED_UNTIL_G10',reason='LATE_NUMERIC_IMPORT',stage_failed='FIXTURE',error_type='NativeBlocked'))
    def poll(self): return 2 if self.scenario=='late_import' else 37
    def cleanup(self): return True
    def close(self): self.closed=True


@pytest.fixture
def runner_fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'source_manifest',lambda:{'source_digest':'fixture'})
    monkeypatch.setattr(runner,'protected_snapshot',lambda:{'fixture':True})
    monkeypatch.setattr(runner,'environment',lambda:{'fixture':True})
    monkeypatch.setattr(runner,'DiagnosticJob',FakeJob)
    return tmp_path


@pytest.mark.parametrize('scenario,status',[('crash','FAILED'),('late_import','BLOCKED')])
def test_ENV12_failure_finalization_and_no_stale_pass(runner_fixture,scenario,status):
    p=runner.qualify('failure',scenario)
    summary=json.loads((p/'run_summary.json').read_text())
    assert summary['status']==status and summary['lifecycle']=='FAILED' and summary['job_empty_verified']
    assert runner.verify_evidence(p)
    old={x.name:x.read_bytes() for x in p.iterdir()}
    with pytest.raises(FileExistsError): runner.qualify('failure',scenario)
    assert old=={x.name:x.read_bytes() for x in p.iterdir()}


def test_ENV13_missing_tampered_extra_and_crlf_evidence(runner_fixture):
    p=runner.qualify('checks','late_import'); f=p/'journal.jsonl'; before=f.read_bytes()
    f.write_bytes(before.replace(b'\n',b'\r\n')); assert runner.verify_evidence(p)
    f.write_bytes(b'tampered'); assert not runner.verify_evidence(p)
    f.write_bytes(before); extra=p/'extra.json'; extra.write_text('{}'); assert not runner.verify_evidence(p)
    extra.unlink(); f.unlink(); assert not runner.verify_evidence(p)


def test_ENV14_finalization_io_error_not_claimed_saved(runner_fixture,monkeypatch):
    original=runner.write_json
    def fail(p,v):
        if p.name=='run_summary.json': raise OSError('fixture write failure')
        return original(p,v)
    monkeypatch.setattr(runner,'write_json',fail)
    with pytest.raises(OSError): runner.qualify('io','late_import')
    assert not runner.verify_evidence(runner.output_path('io'))


def test_ENV15_source_postcheck_change_and_cleanup_failure(runner_fixture,monkeypatch):
    calls=[]
    def changed(): calls.append(1); return {'source_digest':'old' if len(calls)==1 else 'changed'}
    monkeypatch.setattr(runner,'source_manifest',changed)
    monkeypatch.setattr(FakeJob,'cleanup',lambda self:False)
    p=runner.qualify('changed','late_import'); d=json.loads((p/'run_summary.json').read_text())
    assert d['status']=='FAILED' and not d['source_unchanged'] and not d['job_empty_verified']
    assert runner.verify_evidence(p)


def test_ENV16_forged_fit_or_incomplete_native_pass_blocked():
    with pytest.raises(e.NativeBlocked): runner.validate_worker(dict(scenario='normal',real_estimator_fits=1),'normal')
    value=dict(scenario='normal',real_estimator_fits=0,validation_scored=False,b2_authorized=False,
               official_test='SEALED_UNTIL_G10',status='PASS',native_verification='PASS')
    with pytest.raises(e.NativeBlocked): runner.validate_worker(value,'normal')


@pytest.mark.parametrize('method',['snapshot','handles','resolve','file_hash'])
def test_ENV17_native_api_errors_do_not_become_empty_pass(method):
    b=Backend()
    def failed(*args): raise OSError('fixture Win32 failure')
    setattr(b,method,failed)
    with pytest.raises(OSError): e.collect(b,['runtime_get_threads'])


def test_ENV18_context_entry_failure_restores_and_warning_blocks(fixture_session,monkeypatch):
    s=session(fixture_session)
    def fail(self): raise RuntimeWarning('fixture limit readback warning')
    monkeypatch.setattr(Limiter,'__enter__',fail)
    with pytest.raises(RuntimeWarning): s.__enter__()
    assert s.controller.restores==1 and s.closed and e._ACTIVE is None


def test_ENV18_info_warning_cannot_start_compute(fixture_session,monkeypatch):
    original=Controller.info
    def warn(self): warnings.warn('fixture missing pool',RuntimeWarning); return original(self)
    monkeypatch.setattr(Controller,'info',warn)
    with pytest.raises(RuntimeWarning): session(fixture_session)


def test_ENV19_preimport_token_is_not_reusable_and_env_drift_fails(fixture_session,monkeypatch):
    with pytest.raises(e.NativeBlocked,match='REUSED'): e.prepare_imports()
    s=session(fixture_session)
    with pytest.raises(e.NativeBlocked,match='THREAD_ENV_DRIFT'):
        with s: monkeypatch.setenv('OMP_NUM_THREADS','2')
    assert s.controller.restores==1 and s.closed


def test_ENV19_dependency_version_drift_blocks_before_controller(fixture_session,monkeypatch):
    monkeypatch.setattr(e,'version',lambda name:'unapproved')
    with pytest.raises(e.NativeBlocked,match='VERSION_MISMATCH'):
        e.NativeSession(_backend=fixture_session[0])


def test_ENV20_timeout_setup_and_close_failures_finalize(runner_fixture,monkeypatch):
    def timeout(self): raise TimeoutError('DIAGNOSTIC_WALL_TIMEOUT')
    monkeypatch.setattr(FakeJob,'poll',timeout)
    p=runner.qualify('timeout','timeout')
    d=json.loads((p/'run_summary.json').read_text())
    assert d['status']=='FAILED' and d['job_empty_verified'] and runner.verify_evidence(p)
    def setup(*args): raise e.NativeBlocked('WIN32_JOB_API_FAILED')
    monkeypatch.setattr(runner,'DiagnosticJob',setup)
    p=runner.qualify('setup','normal'); d=json.loads((p/'run_summary.json').read_text())
    assert d['status']=='BLOCKED' and not d['worker_started'] and runner.verify_evidence(p)


def test_ENV20_close_error_not_pass(runner_fixture,monkeypatch):
    def fail(self): raise OSError('fixture close failure')
    monkeypatch.setattr(FakeJob,'close',fail)
    p=runner.qualify('close','late_import'); d=json.loads((p/'run_summary.json').read_text())
    assert d['status']=='FAILED' and runner.verify_evidence(p)


def test_ENV21_alias_detected_before_checksum_read(runner_fixture,monkeypatch):
    p=runner.qualify('alias','late_import'); original=Path.resolve
    def alias(self,*args,**kwargs):
        if self.name=='journal.jsonl': return p.parent/'unopened.csv'
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'resolve',alias)
    assert not runner.verify_evidence(p)


def test_ENV22_direct_worker_has_no_unbound_execution_entrypoint(monkeypatch):
    monkeypatch.delenv('SC_ENV_WORKER_NONCE',raising=False)
    with pytest.raises(e.NativeBlocked,match='HANDSHAKE_MISSING'):
        runner.worker('never_created','normal')


def test_ENV23_fixture_context_never_claims_real_native_gate(fixture_session):
    s=session(fixture_session)
    with s: pass
    value=dict(scenario='normal',real_estimator_fits=0,validation_scored=False,b2_authorized=False,
               official_test='SEALED_UNTIL_G10',status='PASS',native_verification='PASS',session=s.public())
    with pytest.raises(e.NativeBlocked,match='NATIVE_COMPLETION_MISSING'):
        runner.validate_worker(value,'normal')


def test_ENV24_python_worker_thread_cannot_claim_main_thread_proof(fixture_session,monkeypatch):
    monkeypatch.setattr(e.threading,'current_thread',lambda:object())
    with pytest.raises(e.NativeBlocked,match='MAIN_THREAD_REQUIRED'): session(fixture_session)

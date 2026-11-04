"""Standalone Windows native-pool verification. Does not authorize real execution.

Only the collector is replaced in a local subclass. Installed threadpoolctl,
ctypes, the accepted B1 worker and process DLL search settings stay unchanged.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import sys
import threading
import warnings

THREAD_ENV = {k: "1" for k in ("OMP_NUM_THREADS", "OMP_THREAD_LIMIT",
    "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}
THREAD_ENV.update(OMP_DYNAMIC="FALSE", MKL_DYNAMIC="FALSE")
THREADPOOLCTL_SHA256 = "e5f119e394193e206655bec4b993ef0bb40b0fbb2f22c92bd5b2d70a622bb518"
RUNTIMES = {
    "libscipy_openblas64_-63c857e738469261263c764a36be9436.dll":
        ("63c857e738469261263c764a36be9436ebdeaa272e340a828f42047a97131080", "blas", "openblas"),
    "libscipy_openblas-64eda39e79589aedb16f58e5547eb599.dll":
        ("64eda39e79589aedb16f58e5547eb599f0b5855505d56b9d40022e2eee354a0b", "blas", "openblas"),
    "vcomp140.dll":
        ("95d4ce4a6802d1e18b5e0e1722cc30ea72ca7e033f83828f05c0b7b993fe7cbf", "openmp", "openmp"),
}
_PREPARED_PID = None
_ACTIVE = None
_HOOK_INSTALLED = False


class NativeBlocked(ValueError):
    """A stable reason code; never contains private paths or raw exceptions."""


def require(condition, reason):
    if not condition:
        raise NativeBlocked(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def path_key(path):
    return os.path.normcase(os.path.realpath(path))


def check_import_contract(modules, environment):
    require(all(environment.get(k) == v for k, v in THREAD_ENV.items()), "THREAD_ENV_MISMATCH")
    require(not any(n.split(".")[0] in {"numpy", "scipy", "sklearn"} for n in modules),
            "NUMERIC_IMPORT_BEFORE_ENV_EVIDENCE")


def prepare_imports():
    """Call once in the fresh diagnostic worker, before numerical imports."""
    global _PREPARED_PID
    require(_PREPARED_PID is None, "PREIMPORT_EVIDENCE_REUSED")
    check_import_contract(sys.modules, os.environ)
    _PREPARED_PID = os.getpid()


def _import_guard(event, args):
    if _ACTIVE is None:
        return
    if event == "import" and args and str(args[0]).split(".")[0] in {"numpy", "scipy", "sklearn"}:
        if args[0] not in sys.modules:
            raise NativeBlocked("LATE_NUMERIC_IMPORT")
    if event == "import" and len(args) > 1 and isinstance(args[1], str):
        if Path(args[1]).suffix.casefold() in {".pyd", ".dll"}:
            raise NativeBlocked("LATE_NATIVE_EXTENSION_IMPORT")
    if event == "ctypes.dlopen":
        raise NativeBlocked("LATE_CTYPES_LIBRARY_LOAD")


def bounded_wide_path(handle, first, fallback):
    """Callbacks return (length, string); no snapshot string is trusted."""
    for size in (260, 32768):
        n, value = first(handle, size)
        if n and n < size - 1:
            require(len(value) == n, "WIDE_PATH_LENGTH_MISMATCH")
            return value
    n, value = fallback(handle, 32768)
    require(n and n < 32767 and len(value) == n, "WIDE_PATH_UNRESOLVED_OR_TRUNCATED")
    return value


class Win32Modules:
    """Toolhelp handles reconciled with independent PSAPI enumeration."""
    def __init__(self):
        require(os.name == "nt" and C.sizeof(C.c_void_p) == 8, "WINDOWS_X64_REQUIRED")
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.ps = C.WinDLL("psapi", use_last_error=True)
        specs = {
            "GetCurrentProcess": ([], W.HANDLE),
            "CreateToolhelp32Snapshot": ([W.DWORD, W.DWORD], W.HANDLE),
            "Module32FirstW": ([W.HANDLE, C.c_void_p], W.BOOL),
            "Module32NextW": ([W.HANDLE, C.c_void_p], W.BOOL),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "GetModuleFileNameW": ([W.HMODULE, W.LPWSTR, W.DWORD], W.DWORD),
            "GetModuleHandleW": ([W.LPCWSTR], W.HMODULE),
            "GetProcAddress": ([W.HMODULE, C.c_char_p], C.c_void_p),
        }
        for name, (args, result) in specs.items():
            fn = getattr(self.k, name); fn.argtypes = args; fn.restype = result
        self.ps.EnumProcessModulesEx.argtypes = [W.HANDLE, C.c_void_p, W.DWORD,
                                                 C.POINTER(W.DWORD), W.DWORD]
        self.ps.EnumProcessModulesEx.restype = W.BOOL
        self.ps.GetModuleFileNameExW.argtypes = [W.HANDLE, W.HMODULE, W.LPWSTR, W.DWORD]
        self.ps.GetModuleFileNameExW.restype = W.DWORD

    def snapshot(self):
        class Entry(C.Structure):
            _fields_ = [("size", W.DWORD), ("module_id", W.DWORD), ("pid", W.DWORD),
                ("global_use", W.DWORD), ("process_use", W.DWORD),
                ("address", C.POINTER(C.c_byte)), ("module_size", W.DWORD),
                ("handle", W.HMODULE), ("name", C.c_wchar * 256), ("path", C.c_wchar * 260)]
        handle = None
        for _ in range(4):
            handle = self.k.CreateToolhelp32Snapshot(0x18, os.getpid())
            if handle not in (None, W.HANDLE(-1).value):
                break
            require(C.get_last_error() == 24, "SNAPSHOT_API_FAILED")
        require(handle not in (None, W.HANDLE(-1).value), "SNAPSHOT_RETRY_EXHAUSTED")
        result = []
        try:
            item = Entry(); item.size = C.sizeof(item)
            require(self.k.Module32FirstW(handle, C.byref(item)), "SNAPSHOT_FIRST_FAILED")
            while True:
                result.append((int(item.handle), item.path))
                if not self.k.Module32NextW(handle, C.byref(item)):
                    require(C.get_last_error() == 18, "SNAPSHOT_NEXT_FAILED")
                    break
        finally:
            require(self.k.CloseHandle(handle), "SNAPSHOT_CLOSE_FAILED")
        return result

    def handles(self):
        for count in (256, 1024, 4096):
            array = (W.HMODULE * count)(); needed = W.DWORD()
            require(self.ps.EnumProcessModulesEx(self.k.GetCurrentProcess(), array,
                    C.sizeof(array), C.byref(needed), 3), "PSAPI_ENUM_FAILED")
            if needed.value <= C.sizeof(array):
                require(needed.value % C.sizeof(W.HMODULE) == 0, "PSAPI_SIZE_INVALID")
                return [int(h) for h in array[:needed.value // C.sizeof(W.HMODULE)]]
        raise NativeBlocked("PSAPI_ENUM_TRUNCATED")

    def resolve(self, handle):
        def first(h, size):
            buf = C.create_unicode_buffer(size)
            n = self.k.GetModuleFileNameW(h, buf, size)
            return int(n), buf.value
        def fallback(h, size):
            buf = C.create_unicode_buffer(size)
            n = self.ps.GetModuleFileNameExW(self.k.GetCurrentProcess(), h, buf, size)
            return int(n), buf.value
        return bounded_wide_path(handle, first, fallback)

    def loaded_handle(self, path):
        return self.k.GetModuleHandleW(path)

    def exists(self, path):
        return Path(path).is_file()

    def file_hash(self, path):
        return digest(Path(path).read_bytes())

    def has_symbol(self, handle, symbol):
        return bool(self.k.GetProcAddress(handle, symbol.encode("ascii")))


@dataclass(frozen=True)
class Runtime:
    handle: int
    path: str
    sha256: str
    snapshot_matches_wide: bool

    def identity(self):
        return self.handle, path_key(self.path), self.sha256

    def public(self):
        return {"name": Path(self.path).name, "sha256": self.sha256,
                "snapshot_matches_wide": self.snapshot_matches_wide,
                "path_characters": len(self.path), "ascii_path": self.path.isascii()}


def collect(backend, symbols):
    snapshot = backend.snapshot()
    require(snapshot, "EMPTY_SNAPSHOT")
    handles = [h for h, _ in snapshot]
    require(all(type(h) is int and h > 0 for h in handles), "INVALID_MODULE_HANDLE")
    require(len(handles) == len(set(handles)), "DUPLICATE_SNAPSHOT_HANDLE")
    independent = backend.handles()
    require(len(independent) == len(set(independent)) and set(handles) == set(independent),
            "SNAPSHOT_PSAPI_MISMATCH_OR_RACE")
    rows = []
    for handle, snapshot_path in snapshot:
        path = backend.resolve(handle)
        require(isinstance(path, str) and path and "?" not in path and "\x00" not in path,
                "INVALID_WIDE_PATH")
        name = Path(path).name.lower()
        hinted = Path(path).suffix.lower() == ".dll" and any(t in name for t in
            ("blas", "mkl", "blis", "vcomp", "libomp", "libiomp", "libgomp"))
        exported = any(backend.has_symbol(handle, s) for s in symbols)
        if not hinted and not exported:
            continue
        require(name in RUNTIMES, "UNKNOWN_NATIVE_RUNTIME")
        require(exported, "NATIVE_RUNTIME_SYMBOLS_MISSING")
        require(backend.exists(path), "NATIVE_PATH_MISSING")
        require(backend.loaded_handle(path) == handle, "MODULE_PATH_HANDLE_MISMATCH")
        value = backend.file_hash(path)
        require(value == RUNTIMES[name][0], "NATIVE_DLL_HASH_MISMATCH")
        require(backend.resolve(handle) == path and backend.loaded_handle(path) == handle,
                "MODULE_CHANGED_DURING_HASH")
        rows.append(Runtime(handle, path, value, snapshot_path == path))
    require({Path(r.path).name.lower() for r in rows} == set(RUNTIMES) and len(rows) == len(RUNTIMES),
            "NATIVE_RUNTIME_MISSING_OR_DUPLICATE")
    require(len({path_key(r.path) for r in rows}) == len(rows), "DUPLICATE_NATIVE_PATH")
    return sorted(rows, key=lambda r: Path(r.path).name.lower())


def validate_info(rows, info, controllers):
    require(isinstance(info, list) and len(info) == len(rows) == len(controllers),
            "CONTROLLER_COVERAGE_MISMATCH")
    seen = set()
    lookup = {path_key(r.path): r for r in rows}
    for value, controller in zip(info, controllers):
        key = path_key(value.get("filepath", ""))
        require(key in lookup and key not in seen, "CONTROLLER_PATH_MISMATCH_OR_DUPLICATE")
        seen.add(key); row = lookup[key]
        expected = RUNTIMES[Path(row.path).name.lower()]
        require(value.get("user_api") == expected[1] and value.get("internal_api") == expected[2],
                "CONTROLLER_API_MISMATCH")
        require(type(value.get("num_threads")) is int and value["num_threads"] == 1,
                "NATIVE_THREADS_NOT_ONE")
        require(controller.dynlib._handle == row.handle, "CONTROLLER_HANDLE_MISMATCH")
        require(bool(value.get("version")) or expected[1] == "openmp", "NATIVE_VERSION_MISSING")
    require(seen == set(lookup), "CONTROLLER_PARTIAL_INVENTORY")
    return [{"name": Path(v["filepath"]).name, "user_api": v["user_api"],
             "internal_api": v["internal_api"], "num_threads": v["num_threads"],
             "version": v.get("version"), "threading_layer": v.get("threading_layer")}
            for v in info]


class NativeSession:
    """One main-thread diagnostic context; injections are synthetic-test-only."""
    def __init__(self, *, _backend=None, _threadpoolctl=None):
        require(threading.current_thread() is threading.main_thread(), "MAIN_THREAD_REQUIRED")
        require(_PREPARED_PID == os.getpid(), "PREIMPORT_EVIDENCE_MISSING")
        require(all(os.environ.get(k) == v for k, v in THREAD_ENV.items()), "THREAD_ENV_DRIFT")
        self.fixture = _backend is not None or _threadpoolctl is not None
        if _threadpoolctl is None:
            require(version("threadpoolctl") == "3.7.0", "THREADPOOLCTL_VERSION_MISMATCH")
            import threadpoolctl
            require(digest(Path(threadpoolctl.__file__).read_bytes()) == THREADPOOLCTL_SHA256,
                    "THREADPOOLCTL_SOURCE_MISMATCH")
            _threadpoolctl = threadpoolctl
        self.tp = _threadpoolctl
        self.backend = Win32Modules() if _backend is None else _backend
        self.symbols = sorted({s for cls in self.tp._ALL_CONTROLLERS for s in cls.check_symbols})
        require(self.symbols, "NATIVE_SYMBOL_CONTRACT_EMPTY")
        self.initial = collect(self.backend, self.symbols)
        self.checkpoints = []
        self.limiter = None
        self.closed = False
        self.entered = False
        self.controller = self._controller()

    def _controller(self):
        tp, rows = self.tp, self.initial
        class WideController(tp.ThreadpoolController):
            def _load_libraries(self):
                for row in rows:
                    self._make_controller_from_path(row.path)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            controller = WideController()
            validate_info(rows, controller.info(), controller.lib_controllers)
        return controller

    def checkpoint(self, stage):
        require(threading.current_thread() is threading.main_thread(), "MAIN_THREAD_REQUIRED")
        require(not self.closed, "SESSION_CLOSED")
        require(isinstance(stage, str) and stage.isascii() and stage.replace("_", "").isalnum(),
                "INVALID_CHECKPOINT_STAGE")
        require(all(os.environ.get(k) == v for k, v in THREAD_ENV.items()), "THREAD_ENV_DRIFT")
        rows = collect(self.backend, self.symbols)
        require([r.identity() for r in rows] == [r.identity() for r in self.initial],
                "NATIVE_INVENTORY_CHANGED")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            info = self.controller.info()
        public = validate_info(rows, info, self.controller.lib_controllers)
        self.checkpoints.append({"stage": stage, "pools": public})
        return public

    def __enter__(self):
        global _ACTIVE, _HOOK_INSTALLED
        require(not self.entered and not self.closed and _ACTIVE is None, "SESSION_REUSE_OR_CONCURRENCY")
        self.checkpoint("before")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                self.limiter = self.controller.limit(limits=1)
                self.limiter.__enter__()
            if not _HOOK_INSTALLED:
                sys.addaudithook(_import_guard); _HOOK_INSTALLED = True
            _ACTIVE = self
            self.entered = True
            self.checkpoint("during_enter")
            return self
        except BaseException:
            _ACTIVE = None
            if self.limiter is not None:
                self.limiter.__exit__(*sys.exc_info())
            self.closed = True
            raise

    def __exit__(self, kind, value, tb):
        global _ACTIVE
        require(self.entered and not self.closed and _ACTIVE is self, "SESSION_STATE_INVALID")
        try:
            try:
                self.checkpoint("during_exit")
            finally:
                _ACTIVE = None
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    self.limiter.__exit__(kind, value, tb)
            self.checkpoint("after_restore")
        finally:
            _ACTIVE = None
            self.closed = True
        return False

    def public(self):
        return {"kind": "SYNTHETIC_FIXTURE" if self.fixture else "WINDOWS_NATIVE_DIAGNOSTIC",
                "runtimes": [r.public() for r in self.initial], "checkpoints": self.checkpoints,
                "context_closed": self.closed, "real_execution_authorized": False}

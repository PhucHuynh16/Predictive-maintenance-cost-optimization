"""Windows Job Object lifecycle, stdlib only; fail closed on API errors."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import time


class BasicLimits(C.Structure):
    _fields_ = [("process_time", C.c_int64), ("job_time", C.c_int64), ("flags", W.DWORD),
                ("min_ws", C.c_size_t), ("max_ws", C.c_size_t), ("active_limit", W.DWORD),
                ("affinity", C.c_size_t), ("priority", W.DWORD), ("scheduling", W.DWORD)]


class IoCounters(C.Structure):
    _fields_ = [(n, C.c_uint64) for n in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(C.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IoCounters), ("process_memory", C.c_size_t),
                ("job_memory", C.c_size_t), ("peak_process_memory", C.c_size_t), ("peak_job_memory", C.c_size_t)]


class Accounting(C.Structure):
    _fields_ = [(n, C.c_int64) for n in ("user", "kernel", "period_user", "period_kernel")]
    _fields_ += [(n, W.DWORD) for n in ("faults", "total_processes", "active_processes", "terminated_processes")]


class Startup(C.Structure):
    _fields_ = [("cb", W.DWORD), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR), ("title", W.LPWSTR)]
    _fields_ += [(n, W.DWORD) for n in ("x", "y", "xsize", "ysize", "xchars", "ychars", "fill", "flags")]
    _fields_ += [("show", W.WORD), ("reserved_size", W.WORD), ("reserved_ptr", C.POINTER(C.c_byte))]
    _fields_ += [(n, W.HANDLE) for n in ("stdin", "stdout", "stderr")]


class ProcessInfo(C.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]


def kernel():
    if os.name != "nt":
        raise OSError("WINDOWS_JOB_REQUIRED")
    k = C.WinDLL("kernel32", use_last_error=True)
    specs = {
        "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
        "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
        "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
        "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
        "IsProcessInJob": ([W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)], W.BOOL),
        "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD,
                           C.c_void_p, W.LPCWSTR, C.POINTER(Startup), C.POINTER(ProcessInfo)], W.BOOL),
        "ResumeThread": ([W.HANDLE], W.DWORD), "CloseHandle": ([W.HANDLE], W.BOOL),
        "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
        "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
        "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
        "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
    }
    for name, (args, result) in specs.items():
        f = getattr(k, name); f.argtypes = args; f.restype = result
    return k


def check(value):
    if not value:
        raise C.WinError(C.get_last_error())
    return value


def memory_snapshot():
    class Status(C.Structure):
        _fields_ = [("length", W.DWORD), ("load", W.DWORD)]
        _fields_ += [(n, C.c_uint64) for n in ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
    k = kernel(); f = k.GlobalMemoryStatusEx
    f.argtypes = [C.POINTER(Status)]; f.restype = W.BOOL
    s = Status(); s.length = C.sizeof(s); check(f(C.byref(s)))
    return dict(total_physical_bytes=s.total, available_physical_bytes=s.available,
                memory_load_percent=s.load, available_commit_bytes=s.page_available)


class WindowsJob:
    """Assignment/readback before ResumeThread; job includes venv redirector + worker.

    The venv redirector can remain alive waiting for its one Python child. Limit 2
    accounts for this shim, not two concurrent experiment workers. No breakaway.
    """
    def __init__(self, argv, env, cwd, memory_bytes, active_limit=2):
        self.k = kernel(); self.job = None; self.pi = ProcessInfo(); self.closed = False
        self.confirmed = False
        try:
            self.job = check(self.k.CreateJobObjectW(None, None))
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000 | 0x200 | 0x8  # kill-on-close, job memory, active count
            limits.basic.active_limit = active_limit
            limits.job_memory = memory_bytes
            check(self.k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)))
            actual = self.limits()
            if (actual["flags"] != limits.basic.flags or actual["job_memory_bytes"] != memory_bytes
                    or actual["active_process_limit"] != active_limit):
                raise OSError("JOB_LIMIT_READBACK_MISMATCH")
            si = Startup(); si.cb = C.sizeof(si)
            cmd = C.create_unicode_buffer(subprocess.list2cmdline(argv))
            block = C.create_unicode_buffer("\0".join(k + "=" + v for k, v in sorted(env.items(), key=lambda kv: kv[0].upper())) + "\0\0")
            check(self.k.CreateProcessW(str(argv[0]), cmd, None, None, False,
                  0x4 | 0x400 | 0x8000000, block, str(cwd), C.byref(si), C.byref(self.pi)))
            check(self.k.AssignProcessToJobObject(self.job, self.pi.process))
            inside = W.BOOL()
            check(self.k.IsProcessInJob(self.pi.process, self.job, C.byref(inside)))
            if not inside.value:
                raise OSError("WORKER_NOT_CONTAINED")
            self.confirmed = True
        except BaseException:
            # A suspended process must never escape if assignment/readback fails.
            if self.pi.process:
                self.k.TerminateProcess(self.pi.process, 125)
                self.k.WaitForSingleObject(self.pi.process, 5000)
            self.close()
            raise

    def limits(self):
        v = ExtendedLimits()
        check(self.k.QueryInformationJobObject(self.job, 9, C.byref(v), C.sizeof(v), None))
        return dict(flags=v.basic.flags, active_process_limit=v.basic.active_limit,
                    job_memory_bytes=v.job_memory, peak_job_memory_bytes=v.peak_job_memory)

    def accounting(self):
        v = Accounting()
        check(self.k.QueryInformationJobObject(self.job, 1, C.byref(v), C.sizeof(v), None))
        return dict(active_processes=v.active_processes, total_processes=v.total_processes,
                    terminated_processes=v.terminated_processes)

    def resume(self):
        if not self.confirmed:
            raise OSError("JOB_NOT_VERIFIED")
        if self.k.ResumeThread(self.pi.thread) == 0xffffffff:
            raise C.WinError(C.get_last_error())

    def poll(self):
        result = self.k.WaitForSingleObject(self.pi.process, 0)
        if result == 0x102:
            return None
        if result != 0:
            raise OSError("WORKER_WAIT_FAILED")
        code = W.DWORD(); check(self.k.GetExitCodeProcess(self.pi.process, C.byref(code)))
        return code.value

    def terminate(self):
        check(self.k.TerminateJobObject(self.job, 124))

    def wait_empty(self, seconds):
        until = time.perf_counter() + seconds
        while time.perf_counter() < until:
            if self.accounting()["active_processes"] == 0:
                return True
            time.sleep(0.01)
        return self.accounting()["active_processes"] == 0

    def close(self):
        if self.closed:
            return
        for handle in (self.job, self.pi.thread, self.pi.process):
            if handle:
                check(self.k.CloseHandle(handle))
        self.closed = True


def native_inventory():
    """Read loaded numerical runtime DLL identities using Unicode Win32 APIs."""
    k = kernel(); ps = C.WinDLL("psapi", use_last_error=True)
    k.GetCurrentProcess.restype = W.HANDLE
    ps.EnumProcessModules.argtypes = [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]
    ps.EnumProcessModules.restype = W.BOOL
    k.GetModuleFileNameW.argtypes = [W.HANDLE, W.LPWSTR, W.DWORD]
    k.GetModuleFileNameW.restype = W.DWORD
    modules = (W.HANDLE * 2048)(); needed = W.DWORD()
    check(ps.EnumProcessModules(k.GetCurrentProcess(), modules, C.sizeof(modules), C.byref(needed)))
    if needed.value > C.sizeof(modules):
        raise OSError("NATIVE_MODULE_INVENTORY_TRUNCATED")
    paths = []
    for h in modules[:needed.value // C.sizeof(W.HANDLE)]:
        b = C.create_unicode_buffer(32768)
        size = k.GetModuleFileNameW(h, b, len(b)); check(size)
        if size >= len(b) - 1:
            raise OSError("NATIVE_MODULE_PATH_TRUNCATED")
        name = Path(b.value).name.lower()
        if any(token in name for token in ("openblas", "libblas", "mkl", "libiomp", "libomp", "vcomp", "libgomp", "blis")):
            paths.append(b.value)
    return sorted(set(paths))

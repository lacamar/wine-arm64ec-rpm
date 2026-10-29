/* Regression tests for 4K guest pages on 16K host pages (Wine + FEX).
 * Prints "<test>: ok|FAIL ..." per test; exit code = number of failures. */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static int failures;
static volatile LONG fault_code;
static volatile ULONG_PTR fault_addr, fault_pc;

#define CHECK(name, cond, ...) do { if (cond) printf("%s: ok\n", name); \
    else { failures++; printf("%s: FAIL ", name); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* probe_*(addr): access *addr; returns 0, or 1 when it faulted (the handler fakes a ret) */
#ifdef __x86_64__
__asm__(".globl probe_read\nprobe_read:\n xor %eax,%eax\n movb (%rcx),%dl\n ret\n"
        ".globl probe_write\nprobe_write:\n xor %eax,%eax\n movb $0x5a,(%rcx)\n ret\n"
        ".globl div_zero\ndiv_zero:\n xor %eax,%eax\n xor %edx,%edx\n div_insn:\n divl %ecx\n ret\n"
        ".globl moffs_load\nmoffs_load:\n xor %eax,%eax\n moffs_insn:\n movabsl 0x10,%eax\n ret\n");
#else
__asm__(".globl _probe_read\n_probe_read:\n xor %eax,%eax\n mov 4(%esp),%ecx\n movb (%ecx),%dl\n ret\n"
        ".globl _probe_write\n_probe_write:\n xor %eax,%eax\n mov 4(%esp),%ecx\n movb $0x5a,(%ecx)\n ret\n"
        ".globl _div_zero\n_div_zero:\n xor %eax,%eax\n xor %edx,%edx\n mov 4(%esp),%ecx\n _div_insn:\n divl %ecx\n ret\n"
        ".globl _moffs_load\n_moffs_load:\n xor %eax,%eax\n _moffs_insn:\n movl 0x10,%eax\n ret\n");
#endif
int probe_read(volatile void *p);
int probe_write(volatile void *p);
int div_zero(unsigned d);
int moffs_load(void);
extern char div_insn[], moffs_insn[];

static LONG CALLBACK handler(EXCEPTION_POINTERS *ep)
{
    CONTEXT *c = ep->ContextRecord;
    DWORD code = ep->ExceptionRecord->ExceptionCode;

    if (code != EXCEPTION_ACCESS_VIOLATION && code != EXCEPTION_GUARD_PAGE &&
        code != EXCEPTION_INT_DIVIDE_BY_ZERO) return EXCEPTION_CONTINUE_SEARCH;
    fault_code = code;
    fault_pc = (ULONG_PTR)ep->ExceptionRecord->ExceptionAddress;
    fault_addr = ep->ExceptionRecord->NumberParameters >= 2 ? ep->ExceptionRecord->ExceptionInformation[1] : 0;
#ifdef __x86_64__
    c->Rip = *(DWORD64 *)c->Rsp; c->Rsp += 8; c->Rax = 1;
#else
    c->Eip = *(DWORD *)c->Esp; c->Esp += 4; c->Eax = 1;
#endif
    return EXCEPTION_CONTINUE_EXECUTION;
}

static char *alloc(SIZE_T size, DWORD prot)
{
    /* 64K-aligned reservations: page 0-3 share one 16K host page */
    return VirtualAlloc(NULL, size, MEM_RESERVE | MEM_COMMIT, prot);
}

static void test_sysinfo(void)
{
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    CHECK("sysinfo", si.dwPageSize == 0x1000 && si.dwAllocationGranularity == 0x10000,
          "page %#lx granularity %#lx", si.dwPageSize, si.dwAllocationGranularity);
}

static void test_subpage_protect(void)
{
    char *p = alloc(0x10000, PAGE_READWRITE);
    DWORD old;
    MEMORY_BASIC_INFORMATION mbi;
    int f0, f1, f2;

    VirtualProtect(p + 0x1000, 0x1000, PAGE_READONLY, &old);
    f0 = probe_write(p);
    f1 = probe_write(p + 0x1000);
    f2 = probe_write(p + 0x2000);
    VirtualQuery(p + 0x1000, &mbi, sizeof(mbi));
    CHECK("subpage_protect", !f0 && f1 && !f2 && mbi.RegionSize == 0x1000 && mbi.Protect == PAGE_READONLY,
          "faults %d%d%d region %#lx prot %#lx", f0, f1, f2, (unsigned long)mbi.RegionSize, mbi.Protect);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_subpage_noaccess(void)
{
    char *p = alloc(0x10000, PAGE_READWRITE);
    DWORD old;
    int r1, r0;

    VirtualProtect(p + 0x2000, 0x1000, PAGE_NOACCESS, &old);
    r1 = probe_read(p + 0x2000);
    r0 = probe_read(p + 0x3000);
    CHECK("subpage_noaccess", r1 && !r0 && fault_addr == (ULONG_PTR)(p + 0x2000),
          "faults %d%d", r1, r0);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_subpage_decommit(void)
{
    char *p = alloc(0x10000, PAGE_READWRITE);
    int i, zero = 1, kept = 1, fault;

    memset(p, 0xaa, 0x4000);
    VirtualFree(p + 0x1000, 0x1000, MEM_DECOMMIT);
    fault = probe_read(p + 0x1000);
    VirtualAlloc(p + 0x1000, 0x1000, MEM_COMMIT, PAGE_READWRITE);
    for (i = 0; i < 0x1000; i++) zero &= p[0x1000 + i] == 0;
    for (i = 0; i < 0x1000; i++) kept &= (unsigned char)p[i] == 0xaa && (unsigned char)p[0x2000 + i] == 0xaa;
    CHECK("subpage_decommit", fault && zero && kept, "fault %d zero %d neighbours %d", fault, zero, kept);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_guard_page(void)
{
    char *p = alloc(0x10000, PAGE_READWRITE);
    DWORD old;
    int first, second;
    LONG code;

    VirtualProtect(p + 0x1000, 0x1000, PAGE_READWRITE | PAGE_GUARD, &old);
    first = probe_read(p + 0x1000);
    code = fault_code;
    second = probe_read(p + 0x1000);
    CHECK("guard_page", first && code == (LONG)EXCEPTION_GUARD_PAGE && !second && !probe_read(p),
          "first %d code %#lx second %d", first, code, second);
    VirtualFree(p, 0, MEM_RELEASE);
}

static DWORD WINAPI stack_thread(void *arg)
{
    volatile char buf[0xc000];
    buf[0] = buf[sizeof(buf) - 1] = 1;
    return buf[0] + buf[sizeof(buf) - 1];
}

static void test_thread_stack(void)
{
    HANDLE t = CreateThread(NULL, 0x10000, stack_thread, NULL, STACK_SIZE_PARAM_IS_A_RESERVATION, NULL);
    DWORD ret = 0;

    WaitForSingleObject(t, 10000);
    GetExitCodeThread(t, &ret);
    CloseHandle(t);
    CHECK("thread_stack_48k_of_64k", ret == 2, "exit %#lx", ret);
}

typedef int (*fn_t)(void);

static void emit_ret(char *p, int val)
{
    p[0] = 0xb8;                    /* mov eax, imm32 */
    memcpy(p + 1, &val, 4);
    p[5] = 0xc3;                    /* ret */
}

static void test_smc_rwx(void)
{
    char *p = alloc(0x4000, PAGE_EXECUTE_READWRITE);
    int a, b, c, i, stale = 0;

    emit_ret(p, 1); a = ((fn_t)p)();
    emit_ret(p, 2); b = ((fn_t)p)();
    for (i = 3; i < 1000; i++) { emit_ret(p + 0x1000, i); stale += ((fn_t)(p + 0x1000))() != i; }
    emit_ret(p, 3); c = ((fn_t)p)();
    CHECK("smc_rwx", a == 1 && b == 2 && c == 3 && !stale, "%d %d %d stale %d", a, b, c, stale);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_smc_shared_host_page(void)
{
    /* code page next to a data page the program keeps writing: one 16K host page */
    char *p = alloc(0x4000, PAGE_READWRITE);
    DWORD old;
    int i, stale = 0;
    volatile int *data = (int *)(p + 0x2000);

    for (i = 0; i < 200; i++) {
        VirtualProtect(p + 0x1000, 0x1000, PAGE_READWRITE, &old);
        emit_ret(p + 0x1000, i);
        VirtualProtect(p + 0x1000, 0x1000, PAGE_EXECUTE_READ, &old);
        FlushInstructionCache(GetCurrentProcess(), p + 0x1000, 6);
        *data = i;
        stale += ((fn_t)(p + 0x1000))() != i;
        *data = -i;
    }
    CHECK("smc_shared_host_page", !stale, "stale %d", stale);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_div_zero(void)
{
    int f = div_zero(0);
    CHECK("div_zero", f && fault_code == (LONG)EXCEPTION_INT_DIVIDE_BY_ZERO && fault_pc == (ULONG_PTR)div_insn,
          "fault %d code %#lx pc %p expected %p", f, fault_code, (void *)fault_pc, div_insn);
}

static void test_moffs_fault(void)
{
    int f = moffs_load();
    CHECK("moffs_fault_pc", f && fault_code == (LONG)EXCEPTION_ACCESS_VIOLATION && fault_pc == (ULONG_PTR)moffs_insn,
          "fault %d code %#lx pc %p expected %p", f, fault_code, (void *)fault_pc, moffs_insn);
}

static volatile LONG spin_stop;
static volatile ULONG_PTR spin_count;

static DWORD WINAPI spin_thread(void *arg)
{
    while (!spin_stop) spin_count++;
    return 0;
}

static void test_suspend_spin(void)
{
    HANDLE t = CreateThread(NULL, 0, spin_thread, NULL, 0, NULL);
    CONTEXT ctx;
    int i, ok = 0;
    DWORD start = GetTickCount();

    Sleep(50);
    for (i = 0; i < 50 && GetTickCount() - start < 20000; i++) {
        ULONG_PTR before;
        if (SuspendThread(t) == (DWORD)-1) break;
        ctx.ContextFlags = CONTEXT_CONTROL;
        if (!GetThreadContext(t, &ctx)) break; /* waits until the thread is actually stopped */
        before = spin_count;
        Sleep(5);
        if (spin_count == before) ok++;
        ResumeThread(t);
    }
    spin_stop = 1;
    WaitForSingleObject(t, 5000);
    CloseHandle(t);
    CHECK("suspend_spin_loop", ok == 50, "%d/50 suspends held", ok);
}

static void test_file_mapping(void)
{
    char path[MAX_PATH], buf[16] = {0};
    HANDLE f, m;
    char *v;
    DWORD n;
    int ok;

    GetTempPathA(sizeof(path), path);
    strcat(path, "hostpage-map.bin");
    f = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_FLAG_DELETE_ON_CLOSE, NULL);
    m = CreateFileMappingA(f, NULL, PAGE_READWRITE, 0, 0x30000, NULL);
    v = MapViewOfFile(m, FILE_MAP_WRITE, 0, 0x10000, 0x1000);
    strcpy(v + 0x800, "hostpage");
    UnmapViewOfFile(v);
    SetFilePointer(f, 0x10800, NULL, FILE_BEGIN);
    ReadFile(f, buf, 8, &n, NULL);
    ok = !strcmp(buf, "hostpage");
    CloseHandle(m);
    CloseHandle(f);
    CHECK("file_mapping_4k_view", ok, "read back '%s'", buf);
}

#ifdef SHARED_SECTION
/* own image: a loader that can't map it must not hide the other tests */
/* big enough to hold a whole 16K host page, which is the part that can be shared */
__attribute__((section(".shr"), shared)) volatile LONG shared_area[0x10000 / sizeof(LONG)] = {1};
#define shared_value shared_area[0x8000 / sizeof(LONG)]

static void test_shared_section(const char *self)
{
    char cmd[MAX_PATH + 32];
    STARTUPINFOA si = {sizeof(si)};
    PROCESS_INFORMATION pi;
    DWORD code = 99;

    shared_value = 0x1234;
    snprintf(cmd, sizeof(cmd), "\"%s\" child", self);
    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, 30000);
        GetExitCodeProcess(pi.hProcess, &code);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
    }
    CHECK("shared_section", code == 0 && shared_value == 0x5678, "child exit %lu value %#lx", code, shared_value);
}

#endif

int main(int argc, char **argv)
{
#ifdef SHARED_SECTION
    if (argc > 1 && !strcmp(argv[1], "child")) {
        if (shared_value != 0x1234) return 1;
        shared_value = 0x5678;
        return 0;
    }
    setvbuf(stdout, NULL, _IONBF, 0);
    test_shared_section(argv[0]);
#else
    setvbuf(stdout, NULL, _IONBF, 0);
    AddVectoredExceptionHandler(1, handler);
    test_sysinfo();
    test_subpage_protect();
    test_subpage_noaccess();
    test_subpage_decommit();
    test_guard_page();
    test_thread_stack();
    test_smc_rwx();
    test_smc_shared_host_page();
    test_div_zero();
    test_moffs_fault();
    test_suspend_spin();
    test_file_mapping();
#endif
    printf("done\n");
    return failures;
}

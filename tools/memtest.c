#include <windows.h>
#include <stdio.h>
#include <string.h>

#define PG 4096

int probe_read(const volatile void *p);
int probe_write(volatile void *p);
extern char probe_read_insn[], probe_write_insn[], probe_fail[];

#ifdef _WIN64
__asm__(".globl probe_read\nprobe_read:\n"
        ".globl probe_read_insn\nprobe_read_insn:\n movzbl (%rcx),%eax\n xorl %eax,%eax\n ret\n"
        ".globl probe_write\nprobe_write:\n"
        ".globl probe_write_insn\nprobe_write_insn:\n movb $0x5a,(%rcx)\n xorl %eax,%eax\n ret\n"
        ".globl probe_fail\nprobe_fail:\n movl $1,%eax\n ret\n");
#define PC(ctx) ((ctx)->Rip)
#else
__asm__(".globl _probe_read\n_probe_read:\n movl 4(%esp),%ecx\n"
        ".globl _probe_read_insn\n_probe_read_insn:\n movzbl (%ecx),%eax\n xorl %eax,%eax\n ret\n"
        ".globl _probe_write\n_probe_write:\n movl 4(%esp),%ecx\n"
        ".globl _probe_write_insn\n_probe_write_insn:\n movb $0x5a,(%ecx)\n xorl %eax,%eax\n ret\n"
        ".globl _probe_fail\n_probe_fail:\n movl $1,%eax\n ret\n");
#define PC(ctx) ((ctx)->Eip)
#endif

static volatile DWORD last_code;
static volatile LONG overflowed;
static int passes, fails;

static void overflow_exit(void)
{
    ExitThread(0);
}

static LONG CALLBACK handler(EXCEPTION_POINTERS *ep)
{
    CONTEXT *ctx = ep->ContextRecord;
    DWORD code = ep->ExceptionRecord->ExceptionCode;

    if (code == STATUS_STACK_OVERFLOW)
    {
        overflowed = 1;
        PC(ctx) = (ULONG_PTR)overflow_exit;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (PC(ctx) == (ULONG_PTR)probe_read_insn || PC(ctx) == (ULONG_PTR)probe_write_insn)
    {
        last_code = code;
        PC(ctx) = (ULONG_PTR)probe_fail;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

static void check(const char *name, int ok, const char *fmt, ...)
{
    char buf[256] = "";
    va_list args;

    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    printf("%s %-28s %s\n", ok ? "PASS" : "FAIL", name, buf);
    if (ok) passes++; else fails++;
}

static int read_code(const void *p)
{
    last_code = 0;
    return probe_read(p) ? (int)last_code : 0;
}

static int write_code(void *p)
{
    last_code = 0;
    return probe_write(p) ? (int)last_code : 0;
}

static char *alloc64k(void)
{
    char *p = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    memset(p, 0xaa, 0x10000);
    return p;
}

static void test_noaccess(void)
{
    char *p = alloc64k();
    DWORD old;
    int c;

    VirtualProtect(p + PG, PG, PAGE_NOACCESS, &old);
    c = read_code(p + PG);
    check("noaccess read", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    c = write_code(p + PG);
    check("noaccess write", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    c = read_code(p);
    check("noaccess neighbour read", c == 0, "code %#x", c);
    c = write_code(p + 2 * PG);
    check("noaccess neighbour write", c == 0, "code %#x", c);
    VirtualProtect(p + PG, PG, PAGE_READWRITE, &old);
    check("noaccess data kept", (unsigned char)p[PG + 100] == 0xaa, "byte %#x", (unsigned char)p[PG + 100]);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_readonly(void)
{
    char *p = alloc64k();
    DWORD old;
    int c;

    VirtualProtect(p + PG, PG, PAGE_READONLY, &old);
    c = write_code(p + PG + 8);
    check("readonly write", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    check("readonly unchanged", (unsigned char)p[PG + 8] == 0xaa, "byte %#x", (unsigned char)p[PG + 8]);
    c = read_code(p + PG);
    check("readonly read", c == 0, "code %#x", c);
    c = write_code(p);
    check("readonly neighbour write", c == 0, "code %#x", c);
    c = write_code(p + 3 * PG);
    check("readonly neighbour2 write", c == 0, "code %#x", c);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_guard(void)
{
    char *p = alloc64k();
    MEMORY_BASIC_INFORMATION mbi;
    DWORD old;
    int c;

    VirtualProtect(p + 2 * PG, PG, PAGE_READWRITE | PAGE_GUARD, &old);
    c = write_code(p + 3 * PG);
    check("guard neighbour write", c == 0, "code %#x", c);
    c = read_code(p + PG);
    check("guard neighbour read", c == 0, "code %#x", c);
    VirtualQuery(p + 2 * PG, &mbi, sizeof(mbi));
    check("guard still set", !!(mbi.Protect & PAGE_GUARD), "protect %#lx", mbi.Protect);
    c = read_code(p + 2 * PG);
    check("guard first touch", c == STATUS_GUARD_PAGE_VIOLATION, "code %#x", c);
    c = read_code(p + 2 * PG);
    check("guard second touch", c == 0, "code %#x", c);
    VirtualQuery(p + 2 * PG, &mbi, sizeof(mbi));
    check("guard cleared", !(mbi.Protect & PAGE_GUARD), "protect %#lx", mbi.Protect);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_decommit(void)
{
    char *p = alloc64k();
    int c, i, zero = 1;

    VirtualFree(p + PG, PG, MEM_DECOMMIT);
    c = read_code(p + PG);
    check("decommit read", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    c = read_code(p);
    check("decommit neighbour read", c == 0 && (unsigned char)p[0] == 0xaa, "code %#x byte %#x", c, (unsigned char)p[0]);
    VirtualAlloc(p + PG, PG, MEM_COMMIT, PAGE_READWRITE);
    for (i = 0; i < PG; i++) if (p[PG + i]) { zero = 0; break; }
    check("recommit zeroed", zero, "first nonzero at %d", zero ? -1 : i);
    check("recommit neighbours kept", (unsigned char)p[PG - 1] == 0xaa && (unsigned char)p[2 * PG] == 0xaa, "");
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_sparse_commit(void)
{
    char *p = VirtualAlloc(NULL, 0x10000, MEM_RESERVE, PAGE_NOACCESS);
    int c;

    VirtualAlloc(p + 3 * PG, PG, MEM_COMMIT, PAGE_READWRITE);
    c = write_code(p + 3 * PG);
    check("sparse commit write", c == 0, "code %#x", c);
    c = read_code(p + 2 * PG);
    check("sparse reserved read", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    c = write_code(p);
    check("sparse reserved write", c == EXCEPTION_ACCESS_VIOLATION, "code %#x", c);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_query(void)
{
    static const DWORD prot[] = { PAGE_READWRITE, PAGE_READONLY, PAGE_NOACCESS, PAGE_EXECUTE_READ,
                                  PAGE_READWRITE, PAGE_EXECUTE_READWRITE, PAGE_READONLY, PAGE_READWRITE };
    char *p = alloc64k();
    MEMORY_BASIC_INFORMATION mbi;
    DWORD old;
    int i, ok = 1;

    for (i = 0; i < 8; i++) VirtualProtect(p + i * PG, PG, prot[i], &old);
    for (i = 0; i < 8; i++)
    {
        VirtualQuery(p + i * PG, &mbi, sizeof(mbi));
        if (mbi.Protect != prot[i] || (ULONG_PTR)mbi.BaseAddress != (ULONG_PTR)p + i * PG || (i < 7 && mbi.RegionSize != PG))
        {
            check("query per page", 0, "page %d protect %#lx size %#lx", i, mbi.Protect, (unsigned long)mbi.RegionSize);
            ok = 0;
            break;
        }
    }
    if (ok) check("query per page", 1, "");
    VirtualProtect(p + 3 * PG, PG, PAGE_READWRITE, &old);
    check("protect old value", old == PAGE_EXECUTE_READ, "old %#lx", old);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_write_watch(void)
{
    char *p = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT | MEM_WRITE_WATCH, PAGE_READWRITE);
    void *pages[16];
    ULONG_PTR count = 16;
    ULONG gran;

    ResetWriteWatch(p, 0x10000);
    p[2 * PG + 5] = 1;
    GetWriteWatch(0, p, 0x10000, pages, &count, &gran);
    check("writewatch single", count == 1 && pages[0] == p + 2 * PG, "count %lu first %p base %p", (unsigned long)count, count ? pages[0] : NULL, p);
    p[5 * PG] = 1;
    count = 16;
    GetWriteWatch(WRITE_WATCH_FLAG_RESET, p, 0x10000, pages, &count, &gran);
    check("writewatch two", count == 2 && pages[1] == p + 5 * PG, "count %lu", (unsigned long)count);
    count = 16;
    GetWriteWatch(0, p, 0x10000, pages, &count, &gran);
    check("writewatch reset", count == 0, "count %lu", (unsigned long)count);
    p[PG] = 2;
    count = 16;
    GetWriteWatch(0, p, 0x10000, pages, &count, &gran);
    check("writewatch after reset", count == 1 && pages[0] == p + PG, "count %lu", (unsigned long)count);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_readfile_readonly(void)
{
    char path[MAX_PATH], tmp[MAX_PATH], data[3 * PG];
    char *p = alloc64k();
    DWORD old, got = 0;
    HANDLE h;
    BOOL ret;

    GetTempPathA(sizeof(tmp), tmp);
    GetTempFileNameA(tmp, "mt", 0, path);
    h = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_FLAG_DELETE_ON_CLOSE, NULL);
    memset(data, 0x11, sizeof(data));
    WriteFile(h, data, sizeof(data), &got, NULL);
    SetFilePointer(h, 0, NULL, FILE_BEGIN);
    VirtualProtect(p + PG, PG, PAGE_READONLY, &old);
    ret = ReadFile(h, p, 3 * PG, &got, NULL);
    check("readfile into readonly", !ret && GetLastError() == ERROR_NOACCESS, "ret %d err %lu", ret, GetLastError());
    check("readfile readonly untouched", (unsigned char)p[PG + 1] == 0xaa, "byte %#x", (unsigned char)p[PG + 1]);
    CloseHandle(h);
    VirtualFree(p, 0, MEM_RELEASE);
}

static DWORD WINAPI grow_thread(void *arg)
{
    volatile char buf[3000];
    int depth = (int)(ULONG_PTR)arg;

    buf[0] = buf[2999] = (char)depth;
    if (depth > 0) return grow_thread((void *)(ULONG_PTR)(depth - 1)) + buf[0];
    return 0;
}

static DWORD WINAPI overflow_thread(void *arg)
{
    volatile char buf[3000];

    buf[0] = buf[2999] = 1;
    return overflow_thread(arg) + buf[0];
}

static void test_stack(void)
{
    HANDLE t;
    DWORD code = 0;

    t = CreateThread(NULL, 1 << 20, grow_thread, (void *)250, STACK_SIZE_PARAM_IS_A_RESERVATION, NULL);
    WaitForSingleObject(t, 10000);
    GetExitCodeThread(t, &code);
    check("stack growth 750K", code != STILL_ACTIVE, "exit %#lx", code);
    CloseHandle(t);

    overflowed = 0;
    t = CreateThread(NULL, 256 << 10, overflow_thread, NULL, STACK_SIZE_PARAM_IS_A_RESERVATION, NULL);
    WaitForSingleObject(t, 10000);
    GetExitCodeThread(t, &code);
    check("stack overflow detected", overflowed && code != STILL_ACTIVE, "overflowed %ld exit %#lx", overflowed, code);
    CloseHandle(t);
}

static void test_smc_shared_page(void)
{
    static const unsigned char code[] = { 0xb8, 0x11, 0x11, 0x11, 0x11, 0xc3 };
    char *p = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    int (*fn)(void) = (void *)(p + PG);
    DWORD old;
    int i, r1, r2, stale = 0;

    VirtualProtect(p + PG, PG, PAGE_EXECUTE_READWRITE, &old);
    for (i = 0; i < 8; i++)
    {
        memcpy(p + PG, code, sizeof(code));
        *(int *)(p + PG + 1) = 0x1000 + i;
        r1 = fn();
        p[100] = (char)i;
        *(int *)(p + PG + 1) = 0x2000 + i;
        r2 = fn();
        if (r1 != 0x1000 + i || r2 != 0x2000 + i) stale++;
    }
    check("smc rwx beside rw page", !stale, "%d/8 stale", stale);
    VirtualFree(p, 0, MEM_RELEASE);
}

static void test_smc_readonly_code(void)
{
    static const unsigned char code[] = { 0xb8, 0x22, 0x22, 0x22, 0x22, 0xc3 };
    char *p = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    int (*fn)(void) = (void *)(p + 2 * PG);
    DWORD old;
    int r1, r2;

    memcpy(p + 2 * PG, code, sizeof(code));
    VirtualProtect(p + 2 * PG, PG, PAGE_EXECUTE_READ, &old);
    r1 = fn();
    VirtualProtect(p + 2 * PG, PG, PAGE_EXECUTE_READWRITE, &old);
    *(int *)(p + 2 * PG + 1) = 0x33333333;
    VirtualProtect(p + 2 * PG, PG, PAGE_EXECUTE_READ, &old);
    FlushInstructionCache(GetCurrentProcess(), p + 2 * PG, PG);
    r2 = fn();
    check("smc protect-patch-protect", r1 == 0x22222222 && r2 == 0x33333333, "r1 %#x r2 %#x", r1, r2);
    VirtualFree(p, 0, MEM_RELEASE);
}

int main(int argc, char **argv)
{
    AddVectoredExceptionHandler(1, handler);
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("memtest %d-bit\n", (int)sizeof(void *) * 8);
    test_noaccess();
    test_readonly();
    test_guard();
    test_decommit();
    test_sparse_commit();
    test_query();
    test_write_watch();
    test_readfile_readonly();
    test_stack();
    test_smc_readonly_code();
    test_smc_shared_page();
    printf("%d/%d pass\n", passes, passes + fails);
    return fails != 0;
}

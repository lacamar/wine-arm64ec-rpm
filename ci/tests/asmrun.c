/* Runs one FEX unittests/ASM flat binary + its config.bin in-process and compares
 * RegData from the state dump the stage appends (hlt is rewritten to jump there). Exit: 0 pass, 1 fail, 2 crash, 3 setup error, 77 unsupported. */
#include <windows.h>
#include <cpuid.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#pragma pack(push, 1)
struct cfg {
    uint64_t match, ignore, stack, entry;
    uint32_t abi, mode, features, region_off, region_n, reg_off, reg_n, mem_off, mem_n, env_off, env_n;
};
struct regdata { uint32_t n; uint64_t key; uint64_t v[]; };
struct memdata { uint64_t addr; uint32_t len; uint8_t d[]; };
#pragma pack(pop)

#ifdef _WIN64
#define CODE 0x20000000ull
#else
#define CODE 0x10000
#endif
#define PAGE 0x4000
#define STACK_BASE 0xc0000000u

extern void asmrun_stub(void *entry, uintptr_t sp) __asm__("asmrun_stub");
__asm__(".data\n.balign 4\nasmrun_mxcsr: .long 0x1f80\n.text\n"
#ifdef _WIN64
        ".globl asmrun_stub\nasmrun_stub:\n fninit\n ldmxcsr asmrun_mxcsr(%rip)\n cld\n"
        " mov %rdx,%rsp\n push %rcx\n"
        " xor %eax,%eax\n xor %ebx,%ebx\n xor %ecx,%ecx\n xor %edx,%edx\n xor %esi,%esi\n xor %edi,%edi\n xor %ebp,%ebp\n"
        " xor %r8d,%r8d\n xor %r9d,%r9d\n xor %r10d,%r10d\n xor %r11d,%r11d\n xor %r12d,%r12d\n xor %r13d,%r13d\n xor %r14d,%r14d\n xor %r15d,%r15d\n"
        " pxor %xmm0,%xmm0\n pxor %xmm1,%xmm1\n pxor %xmm2,%xmm2\n pxor %xmm3,%xmm3\n pxor %xmm4,%xmm4\n pxor %xmm5,%xmm5\n pxor %xmm6,%xmm6\n pxor %xmm7,%xmm7\n"
        " pxor %xmm8,%xmm8\n pxor %xmm9,%xmm9\n pxor %xmm10,%xmm10\n pxor %xmm11,%xmm11\n pxor %xmm12,%xmm12\n pxor %xmm13,%xmm13\n pxor %xmm14,%xmm14\n pxor %xmm15,%xmm15\n"
        " pushq $0x202\n popfq\n ret\n"
#else
        ".globl asmrun_stub\nasmrun_stub:\n fninit\n ldmxcsr asmrun_mxcsr\n cld\n"
        " mov 4(%esp),%eax\n mov 8(%esp),%ecx\n mov %ecx,%esp\n push %eax\n"
        " xor %eax,%eax\n xor %ebx,%ebx\n xor %ecx,%ecx\n xor %edx,%edx\n xor %esi,%esi\n xor %edi,%edi\n xor %ebp,%ebp\n"
        " pxor %xmm0,%xmm0\n pxor %xmm1,%xmm1\n pxor %xmm2,%xmm2\n pxor %xmm3,%xmm3\n pxor %xmm4,%xmm4\n pxor %xmm5,%xmm5\n pxor %xmm6,%xmm6\n pxor %xmm7,%xmm7\n"
        " pushl $0x202\n popfl\n ret\n"
#endif
);

static uint8_t *cfgbuf;
static struct cfg *cfg;

static void *readfile(const char *p, size_t *len)
{
    FILE *f = fopen(p, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *b = malloc(n + 1);
    if (fread(b, 1, n, f) != (size_t)n) return NULL;
    fclose(f);
    if (len) *len = n;
    return b;
}

static int has_features(uint32_t f)
{
    unsigned a, b, c, d, a7 = 0, b7 = 0, c7 = 0, d7 = 0, a71 = 0, d71 = 0, ec = 0, ed = 0, eb8 = 0;
    __cpuid(1, a, b, c, d);
    if (__get_cpuid_max(0, 0) >= 7) {
        __cpuid_count(7, 0, a7, b7, c7, d7);
        __cpuid_count(7, 1, a71, b, c, d71);
    }
    __cpuid(1, a, b, c, d);
    {
        unsigned x, y, z;
        __cpuid(0x80000001, x, y, ec, ed);
        __cpuid(0x80000008, x, eb8, y, z);
    }
#define BIT(v, n) (((v) >> (n)) & 1)
    int ok[31] = {
        BIT(ed, 31), BIT(ec, 6), BIT(c, 28) && BIT(c, 27), BIT(c, 30), BIT(b7, 29), BIT(eb8, 0),
        BIT(b7, 3), BIT(b7, 8), BIT(b7, 24), 0, BIT(c7, 9), 1, BIT(c, 9), BIT(c, 19), BIT(c, 20),
        BIT(c, 25), BIT(c, 1), BIT(c, 22), BIT(b7, 19), BIT(c, 26), BIT(c7, 22), BIT(b7, 23), BIT(b7, 0),
        0, BIT(a71, 4), BIT(d7, 14), BIT(d71, 5), BIT(d71, 4), BIT(d71, 10), BIT(a71, 23), BIT(a71, 0),
    };
    for (int i = 0; i < 31; i++)
        if ((f >> i & 1) && !ok[i]) return 0;
    return 1;
}

static int alloc_at(uint64_t addr, uint64_t size)
{
    if (VirtualAlloc((void *)(uintptr_t)addr, size, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE)) return 1;
    printf("cannot map 0x%llx+0x%llx (%lu)\n", (unsigned long long)addr, (unsigned long long)size, GetLastError());
    return 0;
}

static int fails;
static void check(const char *name, int idx, uint64_t got, uint64_t exp)
{
    if (got == exp) return;
    fails++;
    printf("%s[%d]: got 0x%016llx != expected 0x%016llx\n", name, idx, (unsigned long long)got, (unsigned long long)exp);
}

static const char *const gprname[] = { "RIP", "RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP",
                                       "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15" };

#define DUMP 0x70000000u
#define FX ((uint8_t *)(uintptr_t)(DUMP + 0x400))
#define AVXFLAG ((uint8_t *)(uintptr_t)(DUMP + 0x90))

static void finish(void)
{
    const uint64_t *g = (const uint64_t *)(uintptr_t)DUMP;
    const uint8_t *d = (const uint8_t *)cfg + cfg->reg_off;
    for (uint32_t i = 0; i < cfg->reg_n; i++) {
        const struct regdata *r = (const struct regdata *)d;
        d += sizeof(*r) + r->n * 8;
        int k = __builtin_ctzll(r->key);
        for (uint32_t j = 0; j < r->n; j++) {
            char n[16];
            uint64_t v = 0;
            if (k >= 1 && k < 17) {
                check(gprname[k], j, g[k + 1], r->v[j]);
            } else if (k >= 17 && k < 33) {
                if (j < 2) memcpy(&v, FX + 160 + (k - 17) * 16 + j * 8, 8);
                else if (*AVXFLAG) memcpy(&v, FX + 576 + (k - 17) * 16 + (j - 2) * 8, 8);
                sprintf(n, "XMM%d", k - 17);
                check(n, j, v, r->v[j]);
            } else if (k >= 35 && k < 43) {
                memcpy(&v, FX + 32 + (((k - 35) - (FX[2 + 1] >> 3 & 7)) & 7) * 16 + j * 8, j ? 2 : 8);
                sprintf(n, "MM%d", k - 35);
                check(n, j, v, r->v[j]);
            }
        }
    }
    printf(fails ? "FAIL\n" : "PASS\n");
    ExitProcess(fails ? 1 : 0);
}

static LONG CALLBACK handler(EXCEPTION_POINTERS *ep)
{
    EXCEPTION_RECORD *er = ep->ExceptionRecord;
    if (er->ExceptionCode == DBG_PRINTEXCEPTION_C || er->ExceptionCode == 0x4001000a) return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT *c = ep->ContextRecord;
    if (er->ExceptionCode == EXCEPTION_PRIV_INSTRUCTION && *(uint8_t *)er->ExceptionAddress == 0xf4) {
        uint64_t *g = (uint64_t *)(uintptr_t)DUMP;
#ifdef _WIN64
        uint64_t v[16] = { c->Rax, c->Rbx, c->Rcx, c->Rdx, c->Rsi, c->Rdi, c->Rbp, c->Rsp,
                           c->R8, c->R9, c->R10, c->R11, c->R12, c->R13, c->R14, c->R15 };
        memcpy(FX, &c->FltSave, 512);
#else
        uint64_t v[16] = { c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp };
        memcpy(FX, c->ExtendedRegisters, 512);
#endif
        memcpy(g + 2, v, sizeof v);
        *AVXFLAG = 0;
        finish();
    }
    printf("exception 0x%lx at %p\n", er->ExceptionCode, er->ExceptionAddress);
    ExitProcess(2);
    return EXCEPTION_CONTINUE_SEARCH;
}

int main(int argc, char **argv)
{
    size_t len;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 3) return 3;
    uint8_t *code = readfile(argv[1], &len);
    cfgbuf = readfile(argv[2], NULL);
    if (!code || !cfgbuf) return 3;
    cfg = (struct cfg *)cfgbuf;
#ifdef _WIN64
    if (cfg->mode != 1) return 77;
#else
    if (cfg->mode == 1) return 77;
#endif
    if (cfg->features & (1u << 9 | 1u << 23)) { printf("unsupported host feature\n"); return 77; }
    if (!has_features(cfg->features)) { printf("unsupported host feature\n"); return 77; }

    if (!VirtualAlloc((void *)CODE, 0x100000, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE)) {
        printf("cannot map code (%lu)\n", GetLastError());
        return 3;
    }
    memcpy((void *)CODE, code, len);
    if (!alloc_at(0xe0000000u, PAGE * 10) || !alloc_at(0xe8000000u - PAGE, PAGE * 2) || !alloc_at(STACK_BASE, 0x10000)) return 3;
    const uint8_t *p = cfgbuf + cfg->region_off;
    for (uint32_t i = 0; i < cfg->region_n; i++, p += 16)
        if (!alloc_at(*(uint64_t *)p, ((*(uint64_t *)(p + 8)) + PAGE - 1) & ~(uint64_t)(PAGE - 1))) return 77;
    p = cfgbuf + cfg->mem_off;
    for (uint32_t i = 0; i < cfg->mem_n; i++) {
        const struct memdata *m = (const struct memdata *)p;
        memcpy((void *)(uintptr_t)m->addr, m->d, m->len);
        p += sizeof(*m) + m->len;
    }
    if (!alloc_at(DUMP, 0x20000)) return 3;
    unsigned a, b, c, d;
    __cpuid(1, a, b, c, d);
    *AVXFLAG = (c >> 26 & 1) && (c >> 28 & 1);
    ((uint64_t *)(uintptr_t)DUMP)[0] = (uintptr_t)finish;
    ((uint64_t *)(uintptr_t)DUMP)[1] = DUMP + 0x20000 - 0x100 - sizeof(void *);
    AddVectoredExceptionHandler(1, handler);
    asmrun_stub((void *)CODE, STACK_BASE + 0x10000);
    return 2;
}

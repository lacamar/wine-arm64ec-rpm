#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char *code_mem;
static int got, expect_off, expect_len;
static DWORD expect_code, last_code;

#ifdef _WIN64
#define PC(ctx) ((ctx)->Rip)
#else
#define PC(ctx) ((ctx)->Eip)
#endif

static void fixup(CONTEXT *ctx, DWORD code)
{
    got++;
    last_code = code;
    if (PC(ctx) != (ULONG_PTR)code_mem + expect_off)
        printf("  handler: pc %#Ix, expected %#Ix\n", (ULONG_PTR)PC(ctx), (ULONG_PTR)code_mem + expect_off);
    PC(ctx) = (ULONG_PTR)code_mem + expect_off + expect_len;
}

#ifdef _WIN64
static LONG CALLBACK handler(EXCEPTION_POINTERS *ep)
{
    ULONG_PTR pc = ep->ContextRecord->Rip;

    if (pc < (ULONG_PTR)code_mem || pc >= (ULONG_PTR)code_mem + 0x1000) return EXCEPTION_CONTINUE_SEARCH;
    fixup(ep->ContextRecord, ep->ExceptionRecord->ExceptionCode);
    return EXCEPTION_CONTINUE_EXECUTION;
}

static int call(void)
{
    return ((int (*)(void))code_mem)();
}
#else
static EXCEPTION_DISPOSITION WINAPI handler(EXCEPTION_RECORD *rec, void *frame, CONTEXT *ctx, void *dispatch)
{
    fixup(ctx, rec->ExceptionCode);
    return ExceptionContinueExecution;
}

struct frame
{
    struct frame *prev;
    void *handler;
};

static int call(void)
{
    struct frame f;
    int ret;

    f.handler = handler;
    __asm__ volatile ("movl %%fs:0,%0" : "=r"(f.prev));
    __asm__ volatile ("movl %0,%%fs:0" :: "r"(&f) : "memory");
    ret = ((int (*)(void))code_mem)();
    __asm__ volatile ("movl %0,%%fs:0" :: "r"(f.prev) : "memory");
    return ret;
}
#endif

struct test
{
    const char *name;
    unsigned char code[24];
    int size, off, len;
    DWORD code_expected;
    int ret;
};

static const struct test tests[] =
{
#ifndef _WIN64
    /* nop; nop; mov %eax,(0); mov $imm,%eax; ret */
    { "write moffs", { 0x90, 0x90, 0xa3, 0, 0, 0, 0, 0xb8, 0x44, 0x33, 0x22, 0x11, 0xc3 }, 13, 2, 5,
      EXCEPTION_ACCESS_VIOLATION, 0x11223344 },
    /* nop; nop; mov (0),%eax; mov $imm,%eax; ret */
    { "read moffs", { 0x90, 0x90, 0xa1, 0, 0, 0, 0, 0xb8, 0x88, 0x77, 0x66, 0x55, 0xc3 }, 13, 2, 5,
      EXCEPTION_ACCESS_VIOLATION, 0x55667788 },
    /* nop; nop; mov %eax,(disp32 0); mov $imm,%eax; ret */
    { "write disp32", { 0x90, 0x90, 0x89, 0x05, 0, 0, 0, 0, 0xb8, 0x21, 0x43, 0x65, 0x07, 0xc3 }, 14, 2, 6,
      EXCEPTION_ACCESS_VIOLATION, 0x07654321 },
#endif
    /* xor %ecx,%ecx; mov (%rcx),%eax; mov $imm,%eax; ret */
    { "read (reg)", { 0x31, 0xc9, 0x8b, 0x01, 0xb8, 0x12, 0x34, 0x56, 0x78, 0xc3 }, 10, 2, 2,
      EXCEPTION_ACCESS_VIOLATION, 0x78563412 },
    /* xor %ecx,%ecx; div %ecx; mov $imm,%eax; ret */
    { "div32", { 0x31, 0xc9, 0xf7, 0xf1, 0xb8, 0xcc, 0xbb, 0xaa, 0x99, 0xc3 }, 10, 2, 2,
      EXCEPTION_INT_DIVIDE_BY_ZERO, 0x99aabbcc },
    /* xor %ecx,%ecx; idiv %ecx; mov $imm,%eax; ret */
    { "idiv32", { 0x31, 0xc9, 0xf7, 0xf9, 0xb8, 0x01, 0x02, 0x03, 0x04, 0xc3 }, 10, 2, 2,
      EXCEPTION_INT_DIVIDE_BY_ZERO, 0x04030201 },
    /* xor %ecx,%ecx; div %cx; mov $imm,%eax; ret */
    { "div16", { 0x31, 0xc9, 0x66, 0xf7, 0xf1, 0xb8, 0x0d, 0x0c, 0x0b, 0x0a, 0xc3 }, 11, 2, 3,
      EXCEPTION_INT_DIVIDE_BY_ZERO, 0x0a0b0c0d },
    /* xor %eax,%eax; pop (%eax); ret -- the faulting store must not move the stack pointer */
    { "pop mem", { 0x31, 0xc0, 0x8f, 0x00, 0xc3 }, 5, 2, 2,
      EXCEPTION_ACCESS_VIOLATION, 0 },
#ifdef _WIN64
    /* push $imm; pop -8(%rsp) (address uses the incremented rsp); mov -8(%rsp),%eax; ret */
    { "pop to stack slot", { 0x68, 0x68, 0x24, 0x57, 0x13, 0x8f, 0x44, 0x24, 0xf8, 0x8b, 0x44, 0x24, 0xf8, 0xc3 }, 14, 0, 0,
      0, 0x13572468 },
#else
    /* push $imm; pop -4(%esp) (address uses the incremented esp); mov -4(%esp),%eax; ret */
    { "pop to stack slot", { 0x68, 0x68, 0x24, 0x57, 0x13, 0x8f, 0x44, 0x24, 0xfc, 0x8b, 0x44, 0x24, 0xfc, 0xc3 }, 14, 0, 0,
      0, 0x13572468 },
#endif
    /* mov $1,%ecx; div %ecx (no fault); mov $imm,%eax; ret */
    { "div nonzero", { 0xb9, 1, 0, 0, 0, 0x31, 0xd2, 0xf7, 0xf1, 0xb8, 0x55, 0x55, 0x55, 0x55, 0xc3 }, 15, 0, 0,
      0, 0x55555555 },
};

int main(int argc, char **argv)
{
    int i, j, fails = 0, rounds = argc > 1 ? atoi(argv[1]) : 20;

    setvbuf(stdout, NULL, _IONBF, 0);
    code_mem = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
#ifdef _WIN64
    AddVectoredExceptionHandler(1, handler);
#endif
    for (i = 0; i < rounds; i++)
    {
        for (j = 0; j < ARRAYSIZE(tests); j++)
        {
            const struct test *t = &tests[j];
            int r;

            memcpy(code_mem, t->code, t->size);
            FlushInstructionCache(GetCurrentProcess(), code_mem, t->size);
            expect_off = t->off;
            expect_len = t->len;
            got = 0;
            last_code = 0;
            r = call();
            if (r != t->ret || got != (t->code_expected != 0) || (got && last_code != t->code_expected))
            {
                printf("round %d %s: ret %#x got %d code %#lx\n", i, t->name, r, got, last_code);
                fails++;
            }
        }
    }
    printf("%d-bit: %d failures in %d rounds\n", (int)sizeof(void *) * 8, fails, rounds);
    return fails != 0;
}

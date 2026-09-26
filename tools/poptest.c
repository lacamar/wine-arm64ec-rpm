#include <windows.h>
#include <stdio.h>
#include <string.h>

static unsigned char *code_mem;
static ULONG_PTR slot[4];

struct test
{
    const char *name;
    unsigned char code[40];
    int size;
};

/* each test leaves its result in rax (64-bit) / eax (32-bit) */
static const struct test tests[] =
{
#ifdef _WIN64
    /* mov $slot,%rcx; push $0x11223344; pop (%rcx); mov (%rcx),%rax; ret */
    { "pop (%rcx)", { 0x48, 0xb9, 0,0,0,0,0,0,0,0, 0x68, 0x44, 0x33, 0x22, 0x11, 0x8f, 0x01, 0x48, 0x8b, 0x01, 0xc3 }, 21 },
    /* mov $slot,%rcx; push $0x5566; pop 8(%rcx); mov 8(%rcx),%rax; ret */
    { "pop 8(%rcx)", { 0x48, 0xb9, 0,0,0,0,0,0,0,0, 0x68, 0x66, 0x55, 0, 0, 0x8f, 0x41, 0x08, 0x48, 0x8b, 0x41, 0x08, 0xc3 }, 23 },
    /* mov $slot,%rcx; xor %edx,%edx; push $0x7788; pop (%rcx,%rdx,8); mov (%rcx),%rax; ret */
    { "pop (%rcx,%rdx,8)", { 0x48, 0xb9, 0,0,0,0,0,0,0,0, 0x31, 0xd2, 0x68, 0x88, 0x77, 0, 0, 0x8f, 0x04, 0xd1, 0x48, 0x8b, 0x01, 0xc3 }, 24 },
    /* mov %rsp,%rdx; push $1; pop (%rcx) with rcx=slot; mov %rsp,%rax; sub %rdx,%rax; ret -> 0 if rsp restored */
    { "rsp after pop mem", { 0x48, 0xb9, 0,0,0,0,0,0,0,0, 0x48, 0x89, 0xe2, 0x6a, 0x01, 0x8f, 0x01, 0x48, 0x89, 0xe0, 0x48, 0x29, 0xd0, 0xc3 }, 24 },
    /* mov $slot,%rcx; push $0x1234; pop %ax to 16-bit? 66 8f 01 = popw (%rcx); then pop remaining 6 bytes: add $6,%rsp; movzwl (%rcx),%eax; ret */
    { "popw (%rcx)", { 0x48, 0xb9, 0,0,0,0,0,0,0,0, 0x68, 0x34, 0x12, 0, 0, 0x66, 0x8f, 0x01, 0x48, 0x83, 0xc4, 0x06, 0x0f, 0xb7, 0x01, 0xc3 }, 26 },
#else
    { "pop (%ecx)", { 0xb9, 0,0,0,0, 0x68, 0x44, 0x33, 0x22, 0x11, 0x8f, 0x01, 0x8b, 0x01, 0xc3 }, 15 },
    { "pop 4(%ecx)", { 0xb9, 0,0,0,0, 0x68, 0x66, 0x55, 0, 0, 0x8f, 0x41, 0x04, 0x8b, 0x41, 0x04, 0xc3 }, 17 },
    { "rsp after pop mem", { 0xb9, 0,0,0,0, 0x89, 0xe2, 0x6a, 0x01, 0x8f, 0x01, 0x89, 0xe0, 0x29, 0xd0, 0xc3 }, 16 },
#endif
};

int main(void)
{
    int i;

    setvbuf(stdout, NULL, _IONBF, 0);
    code_mem = VirtualAlloc(NULL, 0x10000, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    for (i = 0; i < ARRAYSIZE(tests); i++)
    {
        ULONG_PTR addr = (ULONG_PTR)slot, r;

        memcpy(code_mem, tests[i].code, tests[i].size);
#ifdef _WIN64
        memcpy(code_mem + 2, &addr, 8);
#else
        memcpy(code_mem + 1, &addr, 4);
#endif
        memset(slot, 0, sizeof(slot));
        FlushInstructionCache(GetCurrentProcess(), code_mem, tests[i].size);
        r = ((ULONG_PTR (*)(void))code_mem)();
        printf("%-20s %#Ix\n", tests[i].name, r);
    }
    return 0;
}

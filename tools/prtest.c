#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <sys/prctl.h>

#define PR_GET_MEM_MODEL 0x6d4d444c
#define PR_SET_MEM_MODEL 0x4d4d444c
#define PR_ARM64_SET_UNALIGN_ATOMIC 0x46455849

static void show(const char *name, int r)
{
    printf("%-28s %d (%s)\n", name, r, r < 0 ? strerror(errno) : "ok");
}

int main(void)
{
    show("PR_GET_MEM_MODEL", prctl(PR_GET_MEM_MODEL, 0, 0, 0, 0));
    show("PR_SET_MEM_MODEL tso", prctl(PR_SET_MEM_MODEL, 1, 0, 0, 0));
    show("PR_GET_MEM_MODEL", prctl(PR_GET_MEM_MODEL, 0, 0, 0, 0));
    show("PR_ARM64_SET_UNALIGN_ATOMIC", prctl(PR_ARM64_SET_UNALIGN_ATOMIC, 1, 0, 0, 0));
    return 0;
}

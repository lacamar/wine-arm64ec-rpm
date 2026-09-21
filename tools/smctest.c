#include <windows.h>
#include <stdio.h>

#define PAGES 11
#define PAGE 4096

typedef int (*fn_t)(void);

static void emit(unsigned char *p, int value)
{
    p[0] = 0xb8;
    memcpy(p + 1, &value, 4);
    p[5] = 0xc3;
}

int main(void)
{
    unsigned char *mem = VirtualAlloc(NULL, PAGES * PAGE, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    int stale = 0, total = 0;

    for (int i = 0; i < PAGES; i++)
    {
        unsigned char *p = mem + i * PAGE + 16;
        int first, second;

        emit(p, 1000 + i);
        first = ((fn_t)p)();
        emit(p, 2000 + i);
        second = ((fn_t)p)();

        total += 2;
        if (first != 1000 + i) { stale++; printf("page %d initial call        WRONG %d\n", i, first); }
        else printf("page %d initial call        OK\n", i);
        if (second != 2000 + i) { stale++; printf("page %d after in-place patch STALE %d\n", i, second); }
        else printf("page %d after in-place patch OK\n", i);
    }
    printf("%d/%d pass\n", total - stale, total);
    return stale != 0;
}

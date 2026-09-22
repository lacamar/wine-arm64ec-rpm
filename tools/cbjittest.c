#include <windows.h>
#include <stdio.h>

/* fills the emulator's code buffer from inside a user callback, then returns through the syscall that dispatched it */

#define STUB 16

static unsigned count = 400000;
static unsigned total;

static void fill(void)
{
    unsigned char *code = VirtualAlloc(NULL, count * STUB, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

    for (unsigned i = 0; i < count; i++)
    {
        unsigned char *p = code + i * STUB;
        p[0] = 0xb8; memcpy(p + 1, &i, 4); /* mov eax, i */
        p[5] = 0xc3;                       /* ret */
    }
    for (unsigned i = 0; i < count; i++) total += ((unsigned (*)(void))(code + i * STUB))();
    VirtualFree(code, 0, MEM_RELEASE);
}

static LRESULT CALLBACK proc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (msg == WM_CREATE)
    {
        fill();
        return 0;
    }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

int main(int argc, char **argv)
{
    WNDCLASSA wc = { .lpfnWndProc = proc, .hInstance = GetModuleHandleA(NULL), .lpszClassName = "cbjittest" };
    HWND hwnd;

    if (argc > 1) count = atoi(argv[1]);
    RegisterClassA(&wc);
    for (int i = 0; i < 3; i++)
    {
        /* WM_CREATE is a user callback out of NtUserCreateWindowEx, unlike a same-thread SendMessage */
        hwnd = CreateWindowA("cbjittest", "", 0, 0, 0, 1, 1, HWND_MESSAGE, NULL, wc.hInstance, NULL);
        printf("round %d returned\n", i);
        fflush(stdout);
        DestroyWindow(hwnd);
    }
    fill(); /* outside any callback, old buffers can go again */
    printf("ok, %u stubs per round, sum %u\n", count, total);
    return 0;
}

#include <windows.h>
#include <stdio.h>

static volatile LONG stop;
static volatile unsigned counter;

static DWORD WINAPI spin(void *arg)
{
    while (!stop) counter++;
    return 0;
}

int main(int argc, char **argv)
{
    int cycles = argc > 1 ? atoi(argv[1]) : 20;
    HANDLE thread = CreateThread(NULL, 0, spin, NULL, 0, NULL);
    DWORD worst = 0;

    Sleep(200);
    for (int i = 0; i < cycles; i++)
    {
        DWORD t0 = GetTickCount(), dt;
        unsigned a, b;
        CONTEXT ctx;

        if (SuspendThread(thread) == (DWORD)-1) { printf("cycle %d: SuspendThread failed %lu\n", i, GetLastError()); return 1; }
        ctx.ContextFlags = CONTEXT_CONTROL;
        GetThreadContext(thread, &ctx);
        dt = GetTickCount() - t0;
        if (dt > worst) worst = dt;
        a = counter; Sleep(50); b = counter;
        if (a != b) { printf("cycle %d: thread still running while suspended\n", i); return 1; }
        ResumeThread(thread);
        Sleep(20);
        if (counter == b) { printf("cycle %d: thread did not resume\n", i); return 1; }
        printf("cycle %d ok, suspend took %lu ms\n", i, dt);
    }
    stop = 1;
    WaitForSingleObject(thread, 1000);
    printf("%d/%d suspend/resume cycles, worst latency %lu ms\n", cycles, cycles, worst);
    return 0;
}

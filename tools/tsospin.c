#include <windows.h>

static volatile LONG stop;
static volatile unsigned counters[4];

static DWORD WINAPI spin(void *arg)
{
    while (!stop) counters[(UINT_PTR)arg & 3]++;
    return 0;
}

static DWORD WINAPI spawner(void *arg)
{
    HANDLE h = CreateThread(NULL, 0, spin, NULL, 0, NULL);
    WaitForSingleObject(h, INFINITE);
    return 0;
}

int main(int argc, char **argv)
{
    for (int i = 0; i < 2; i++) CreateThread(NULL, 0, spin, NULL, 0, NULL);
    CreateThread(NULL, 0, spawner, NULL, 0, NULL);
    Sleep((argc > 1 ? atoi(argv[1]) : 60) * 1000);
    stop = 1;
    return 0;
}

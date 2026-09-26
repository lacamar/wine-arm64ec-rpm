#include <windows.h>

__attribute__((section(".shr"), shared)) volatile LONG shared_counter = 0;
__attribute__((section(".shr"), shared)) volatile LONG shared_pad[16384] = { 1 };
volatile LONG private_counter = 0;

__declspec(dllexport) volatile LONG *get_shared(void)
{
    return &shared_counter;
}

__declspec(dllexport) volatile LONG *get_shared_mid(void)
{
    return &shared_pad[8192];
}

__declspec(dllexport) volatile LONG *get_private(void)
{
    return &private_counter;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, void *reserved)
{
    return TRUE;
}

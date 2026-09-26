#include <windows.h>
#include <stdio.h>
#include <string.h>

typedef volatile LONG *(*get_fn)(void);

int main(int argc, char **argv)
{
    char dll[MAX_PATH], cmd[MAX_PATH + 16];
    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    MEMORY_BASIC_INFORMATION mbi;
    volatile LONG *shared, *mid, *priv;
    HMODULE mod;
    DWORD code;

    setvbuf(stdout, NULL, _IONBF, 0);
    GetModuleFileNameA(NULL, dll, sizeof(dll));
    strcpy(strrchr(dll, '\\') + 1, sizeof(void *) == 8 ? "shdll64.dll" : "shdll32.dll");
    if (!(mod = LoadLibraryA(dll)))
    {
        printf("LoadLibrary %s failed %lu\n", dll, GetLastError());
        return 2;
    }
    shared = ((get_fn)GetProcAddress(mod, "get_shared"))();
    priv = ((get_fn)GetProcAddress(mod, "get_private"))();
    mid = ((get_fn)GetProcAddress(mod, "get_shared_mid"))();

    if (argc > 1)
    {
        /* child: report what the parent wrote, then write back */
        printf("child: shared %ld mid %ld private %ld\n", *shared, *mid, *priv);
        code = (*mid == 5678) << 1 | (*shared == 1234);
        *shared = 4321;
        *mid = 8765;
        return code;
    }

    VirtualQuery((void *)shared, &mbi, sizeof(mbi));
    printf("shared section at %p protect %#lx type %#lx\n", shared, mbi.Protect, mbi.Type);
    *shared = 1234;
    *mid = 5678;
    *priv = 99;
    sprintf(cmd, "\"%s\" child", argv[0]);
    GetModuleFileNameA(NULL, cmd + 1, MAX_PATH);
    strcat(cmd, "\" child");
    CreateProcessA(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);
    WaitForSingleObject(pi.hProcess, 30000);
    GetExitCodeProcess(pi.hProcess, &code);
    printf("%s shared section start (child %s, parent sees %ld)\n", (code & 1) && *shared == 4321 ? "PASS" : "FAIL",
           code & 1 ? "saw it" : "did not see it", *shared);
    printf("%s shared section middle (child %s, parent sees %ld)\n", (code & 2) && *mid == 8765 ? "PASS" : "FAIL",
           code & 2 ? "saw it" : "did not see it", *mid);
    return code != 3;
}

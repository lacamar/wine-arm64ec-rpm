#include <windows.h>
#include <stdio.h>

#define PG 4096

typedef void *(WINAPI *VirtualAlloc2_fn)(HANDLE, void *, SIZE_T, ULONG, ULONG, MEM_EXTENDED_PARAMETER *, ULONG);
typedef void *(WINAPI *MapViewOfFile3_fn)(HANDLE, HANDLE, void *, ULONG64, SIZE_T, ULONG, ULONG, MEM_EXTENDED_PARAMETER *, ULONG);

static int fails;

static void check(const char *name, int ok, DWORD err)
{
    printf("%s %-36s err %lu\n", ok ? "PASS" : "FAIL", name, err);
    if (!ok) fails++;
}

static void split_test(VirtualAlloc2_fn pVirtualAlloc2, SIZE_T split)
{
    char name[64];
    char *p = pVirtualAlloc2(NULL, NULL, 0x40000, MEM_RESERVE | MEM_RESERVE_PLACEHOLDER, PAGE_NOACCESS, NULL, 0);
    BOOL ret;
    void *q;

    if (!p) { check("reserve placeholder", 0, GetLastError()); return; }
    ret = VirtualFree(p, split, MEM_RELEASE | MEM_PRESERVE_PLACEHOLDER);
    sprintf(name, "split placeholder at %#Ix", split);
    check(name, ret, GetLastError());
    q = pVirtualAlloc2(NULL, p, split, MEM_RESERVE | MEM_COMMIT | MEM_REPLACE_PLACEHOLDER, PAGE_READWRITE, NULL, 0);
    sprintf(name, "commit into %#Ix placeholder", split);
    check(name, q == p, GetLastError());
    if (q) memset(q, 0x5a, split);
    VirtualFree(p, 0, MEM_RELEASE);
    VirtualFree(p + split, 0, MEM_RELEASE);
}

int main(void)
{
    HMODULE kb = GetModuleHandleA("kernelbase.dll");
    VirtualAlloc2_fn pVirtualAlloc2 = (void *)GetProcAddress(kb, "VirtualAlloc2");
    MapViewOfFile3_fn pMapViewOfFile3 = (void *)GetProcAddress(kb, "MapViewOfFile3");
    HANDLE mapping;
    char *p, *v;

    setvbuf(stdout, NULL, _IONBF, 0);
    if (!pVirtualAlloc2 || !pMapViewOfFile3) { printf("no VirtualAlloc2/MapViewOfFile3\n"); return 2; }

    split_test(pVirtualAlloc2, 0x10000);
    split_test(pVirtualAlloc2, 0x4000);
    split_test(pVirtualAlloc2, 0x1000);
    split_test(pVirtualAlloc2, 0x3000);

    /* map a 4K section view into a 4K placeholder */
    mapping = CreateFileMappingA(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, 0x10000, NULL);
    p = pVirtualAlloc2(NULL, NULL, 0x40000, MEM_RESERVE | MEM_RESERVE_PLACEHOLDER, PAGE_NOACCESS, NULL, 0);
    check("split for view (0x10000)", VirtualFree(p, 0x10000, MEM_RELEASE | MEM_PRESERVE_PLACEHOLDER), GetLastError());
    v = pMapViewOfFile3(mapping, NULL, p, 0, 0x10000, MEM_REPLACE_PLACEHOLDER, PAGE_READWRITE, NULL, 0);
    check("view into 64K placeholder", v == p, GetLastError());
    if (v) UnmapViewOfFile(v);
    VirtualFree(p, 0, MEM_RELEASE);
    VirtualFree(p + 0x10000, 0, MEM_RELEASE);

    p = pVirtualAlloc2(NULL, NULL, 0x40000, MEM_RESERVE | MEM_RESERVE_PLACEHOLDER, PAGE_NOACCESS, NULL, 0);
    check("split for view (0x1000)", VirtualFree(p, 0x1000, MEM_RELEASE | MEM_PRESERVE_PLACEHOLDER), GetLastError());
    v = pMapViewOfFile3(mapping, NULL, p, 0, 0x1000, MEM_REPLACE_PLACEHOLDER, PAGE_READWRITE, NULL, 0);
    check("view into 4K placeholder", v == p, GetLastError());

    printf("%d failures\n", fails);
    return fails != 0;
}

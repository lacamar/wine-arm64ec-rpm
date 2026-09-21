#include <windows.h>
#include <d3d9.h>
#include <d3dcommon.h>
#include <stdio.h>

typedef HRESULT (WINAPI *create_effect_t)(IDirect3DDevice9 *, const char *, const void *, void *, DWORD,
                                          void *, void **, ID3D10Blob **);

int main(int argc, char **argv)
{
    D3DPRESENT_PARAMETERS pp = { .Windowed = TRUE, .SwapEffect = D3DSWAPEFFECT_DISCARD, .BackBufferFormat = D3DFMT_UNKNOWN };
    const char *dll = getenv("FXTEST_D3DX") ? getenv("FXTEST_D3DX") : "d3dx9_43.dll";
    IDirect3D9 *d3d = Direct3DCreate9(D3D_SDK_VERSION);
    IDirect3DDevice9 *device = NULL;
    HWND hwnd = CreateWindowA("STATIC", "fxtest", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, NULL, NULL);
    HRESULT hr = IDirect3D9_CreateDevice(d3d, D3DADAPTER_DEFAULT, D3DDEVTYPE_NULLREF, hwnd,
                                         D3DCREATE_SOFTWARE_VERTEXPROCESSING, &pp, &device);
    HMODULE module = LoadLibraryA(dll);
    create_effect_t create = module ? (create_effect_t)GetProcAddress(module, "D3DXCreateEffectFromFileA") : NULL;

    printf("device hr=%08lx %s=%p\n", hr, dll, module);
    if (!create) return 1;

    for (int i = 1; i < argc; i++)
    {
        ID3D10Blob *errors = NULL;
        void *effect = NULL;

        hr = create(device, argv[i], NULL, NULL, 0, NULL, &effect, &errors);
        printf("%s: hr=%08lx effect=%p\n", argv[i], hr, effect);
        if (errors) printf("%s\n", (char *)errors->lpVtbl->GetBufferPointer(errors));
        fflush(stdout);
    }
    return 0;
}

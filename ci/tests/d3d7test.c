/* d3d7test: render with IDirect3DDevice7, read pixels back, print PASS/FAIL
   i686-w64-mingw32-gcc -O2 d3d7test.c -o d3d7test.exe -lddraw -ldxguid -luser32 -lgdi32 */
#define INITGUID
#include <windows.h>
#include <ddraw.h>
#include <d3d.h>
#include <stdio.h>

#define W 256
#define H 256

struct vtx { float x, y, z, rhw; DWORD color; };

static int fail(const char *what, HRESULT hr)
{
    printf("FAIL %s hr=%#lx\n", what, (unsigned long)hr);
    fflush(stdout);
    return 1;
}

static DWORD pixel(IDirectDrawSurface7 *s, int x, int y)
{
    DDSURFACEDESC2 d = { sizeof(d) };
    DWORD v = 0xdeadbeef;
    if (SUCCEEDED(IDirectDrawSurface7_Lock(s, NULL, &d, DDLOCK_WAIT | DDLOCK_READONLY, NULL)))
    {
        v = ((DWORD *)((BYTE *)d.lpSurface + y * d.lPitch))[x] & 0xffffff;
        IDirectDrawSurface7_Unlock(s, NULL);
    }
    return v;
}

int main(void)
{
    IDirectDraw7 *dd;
    IDirect3D7 *d3d;
    IDirect3DDevice7 *dev;
    IDirectDrawSurface7 *rt, *primary;
    IDirectDrawClipper *clip;
    DDSURFACEDESC2 sd = { sizeof(sd) };
    D3DVIEWPORT7 vp = { 0, 0, W, H, 0.0f, 1.0f };
    char path[MAX_PATH] = "?";
    HMODULE mod;
    HWND hwnd;
    HRESULT hr;
    DWORD c, e, start;
    int frames = 0, ok;

    hwnd = CreateWindowA("static", "d3d7test", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 0, 0, W + 16, H + 39, 0, 0, 0, 0);
    if ((hr = DirectDrawCreateEx(NULL, (void **)&dd, &IID_IDirectDraw7, NULL))) return fail("DirectDrawCreateEx", hr);
    if ((mod = GetModuleHandleA("ddraw.dll"))) GetModuleFileNameA(mod, path, sizeof(path));
    printf("ddraw.dll: %s\n", path);
    if ((hr = IDirectDraw7_SetCooperativeLevel(dd, hwnd, DDSCL_NORMAL))) return fail("SetCooperativeLevel", hr);

    sd.dwFlags = DDSD_CAPS;
    sd.ddsCaps.dwCaps = DDSCAPS_PRIMARYSURFACE;
    if ((hr = IDirectDraw7_CreateSurface(dd, &sd, &primary, NULL))) return fail("CreateSurface primary", hr);
    if ((hr = IDirectDraw7_CreateClipper(dd, 0, &clip, NULL))) return fail("CreateClipper", hr);
    IDirectDrawClipper_SetHWnd(clip, 0, hwnd);
    IDirectDrawSurface7_SetClipper(primary, clip);

    memset(&sd, 0, sizeof(sd));
    sd.dwSize = sizeof(sd);
    sd.dwFlags = DDSD_CAPS | DDSD_WIDTH | DDSD_HEIGHT | DDSD_PIXELFORMAT;
    sd.dwWidth = W;
    sd.dwHeight = H;
    sd.ddsCaps.dwCaps = DDSCAPS_OFFSCREENPLAIN | DDSCAPS_3DDEVICE | DDSCAPS_VIDEOMEMORY;
    sd.ddpfPixelFormat.dwSize = sizeof(sd.ddpfPixelFormat);
    sd.ddpfPixelFormat.dwFlags = DDPF_RGB;
    sd.ddpfPixelFormat.dwRGBBitCount = 32;
    sd.ddpfPixelFormat.dwRBitMask = 0xff0000;
    sd.ddpfPixelFormat.dwGBitMask = 0x00ff00;
    sd.ddpfPixelFormat.dwBBitMask = 0x0000ff;
    if ((hr = IDirectDraw7_CreateSurface(dd, &sd, &rt, NULL))) return fail("CreateSurface rt", hr);

    if ((hr = IDirectDraw7_QueryInterface(dd, &IID_IDirect3D7, (void **)&d3d))) return fail("QueryInterface IDirect3D7", hr);
    if ((hr = IDirect3D7_CreateDevice(d3d, &IID_IDirect3DTnLHalDevice, rt, &dev)) &&
        (hr = IDirect3D7_CreateDevice(d3d, &IID_IDirect3DHALDevice, rt, &dev)))
        return fail("CreateDevice", hr);
    IDirect3DDevice7_SetViewport(dev, &vp);
    IDirect3DDevice7_SetRenderState(dev, D3DRENDERSTATE_LIGHTING, FALSE);
    IDirect3DDevice7_SetRenderState(dev, D3DRENDERSTATE_CULLMODE, D3DCULL_NONE);
    IDirect3DDevice7_SetRenderState(dev, D3DRENDERSTATE_ZENABLE, FALSE);

    start = GetTickCount();
    while (GetTickCount() - start < 5000)
    {
        MSG msg;
        struct vtx tri[3] = {
            { W / 2.0f, 16.0f, 0.5f, 1.0f, 0xffff0000 },
            { W - 16.0f, H - 16.0f, 0.5f, 1.0f, 0xffff0000 },
            { 16.0f, H - 16.0f, 0.5f, 1.0f, 0xffff0000 },
        };
        RECT r;

        while (PeekMessageA(&msg, 0, 0, 0, PM_REMOVE)) DispatchMessageA(&msg);
        if ((hr = IDirect3DDevice7_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff0000ff, 1.0f, 0))) return fail("Clear", hr);
        if ((hr = IDirect3DDevice7_BeginScene(dev))) return fail("BeginScene", hr);
        hr = IDirect3DDevice7_DrawPrimitive(dev, D3DPT_TRIANGLELIST, D3DFVF_XYZRHW | D3DFVF_DIFFUSE, tri, 3, 0);
        IDirect3DDevice7_EndScene(dev);
        if (hr) return fail("DrawPrimitive", hr);
        GetClientRect(hwnd, &r);
        MapWindowPoints(hwnd, NULL, (POINT *)&r, 2);
        IDirectDrawSurface7_Blt(primary, &r, rt, NULL, DDBLT_WAIT, NULL);
        frames++;
    }

    c = pixel(rt, W / 2, H / 2);
    e = pixel(rt, 4, 4);
    ok = c == 0xff0000 && e == 0x0000ff;
    printf("frames %d in 5s, center %06lx (want ff0000), corner %06lx (want 0000ff)\n%s\n",
           frames, (unsigned long)c, (unsigned long)e, ok ? "PASS" : "FAIL");
    fflush(stdout);
    return !ok;
}

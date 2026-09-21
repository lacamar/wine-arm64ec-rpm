#include <windows.h>
#include <stdio.h>

static const char *awareness_name(HWND hwnd)
{
    DPI_AWARENESS_CONTEXT ctx = GetWindowDpiAwarenessContext(hwnd);
    if (AreDpiAwarenessContextsEqual(ctx, DPI_AWARENESS_CONTEXT_UNAWARE)) return "unaware";
    if (AreDpiAwarenessContextsEqual(ctx, DPI_AWARENESS_CONTEXT_SYSTEM_AWARE)) return "system";
    if (AreDpiAwarenessContextsEqual(ctx, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)) return "pmv2";
    if (AreDpiAwarenessContextsEqual(ctx, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE)) return "pm";
    return "?";
}

static BOOL CALLBACK monitor_cb(HMONITOR monitor, HDC dc, RECT *rect, LPARAM lp)
{
    MONITORINFOEXA mi = { .cbSize = sizeof(mi) };
    DEVMODEA dm = { .dmSize = sizeof(dm) };

    GetMonitorInfoA(monitor, (MONITORINFO *)&mi);
    EnumDisplaySettingsA(mi.szDevice, ENUM_CURRENT_SETTINGS, &dm);
    printf("monitor %s (%ld,%ld)-(%ld,%ld) mode %lux%lu at (%ld,%ld) dpi %u\n", mi.szDevice,
           mi.rcMonitor.left, mi.rcMonitor.top, mi.rcMonitor.right, mi.rcMonitor.bottom,
           dm.dmPelsWidth, dm.dmPelsHeight, dm.dmPosition.x, dm.dmPosition.y, GetDpiForSystem());
    return TRUE;
}

static BOOL CALLBACK window_cb(HWND hwnd, LPARAM lp)
{
    MONITORINFO mi = { .cbSize = sizeof(mi) };
    char title[256];
    POINT origin = {0, 0};
    RECT rect, client;

    if (!IsWindowVisible(hwnd) || !GetWindowTextA(hwnd, title, sizeof(title))) return TRUE;
    if (!strstr(title, (const char *)lp)) return TRUE;

    GetWindowRect(hwnd, &rect);
    GetClientRect(hwnd, &client);
    ClientToScreen(hwnd, &origin);
    GetMonitorInfoA(MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST), &mi);
    printf("awareness %s hwnd %p '%s'\n rect (%ld,%ld)-(%ld,%ld) client %ldx%ld at (%ld,%ld) dpi %u monitor (%ld,%ld)-(%ld,%ld)\n",
           awareness_name(hwnd), hwnd, title, rect.left, rect.top, rect.right, rect.bottom,
           client.right, client.bottom, origin.x, origin.y, GetDpiForWindow(hwnd),
           mi.rcMonitor.left, mi.rcMonitor.top, mi.rcMonitor.right, mi.rcMonitor.bottom);
    return TRUE;
}

int main(int argc, char **argv)
{
    const char *mode = argc > 2 ? argv[2] : "pmv2";

    SetProcessDpiAwarenessContext(!strcmp(mode, "unaware") ? DPI_AWARENESS_CONTEXT_UNAWARE :
                                  !strcmp(mode, "system") ? DPI_AWARENESS_CONTEXT_SYSTEM_AWARE :
                                  !strcmp(mode, "pm") ? DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE :
                                  DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
    EnumDisplayMonitors(NULL, NULL, monitor_cb, 0);
    EnumWindows(window_cb, (LPARAM)(argc > 1 ? argv[1] : ""));
    return 0;
}

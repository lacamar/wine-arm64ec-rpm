#include <windows.h>
#include <stdio.h>

static void print_window(HWND hwnd, int depth)
{
    char title[256] = "", cls[128] = "";
    DWORD pid = 0;
    RECT rect;

    GetWindowTextA(hwnd, title, sizeof(title));
    GetClassNameA(hwnd, cls, sizeof(cls));
    GetWindowThreadProcessId(hwnd, &pid);
    GetWindowRect(hwnd, &rect);
    printf("%*s%p pid=%lx owner=%p ex=%08lx st=%08lx (%ld,%ld)-(%ld,%ld) '%s' '%s'\n", depth * 2, "", hwnd, pid,
           GetWindow(hwnd, GW_OWNER), GetWindowLongA(hwnd, GWL_EXSTYLE), GetWindowLongA(hwnd, GWL_STYLE),
           rect.left, rect.top, rect.right, rect.bottom, cls, title);
}

static BOOL CALLBACK list_cb(HWND hwnd, LPARAM lp)
{
    if (IsWindowVisible(hwnd)) print_window(hwnd, 0);
    return TRUE;
}

static void list_children(HWND parent, int depth)
{
    for (HWND child = GetWindow(parent, GW_CHILD); child; child = GetWindow(child, GW_HWNDNEXT))
    {
        print_window(child, depth);
        list_children(child, depth + 1);
    }
}

static BOOL CALLBACK find_cb(HWND hwnd, LPARAM lp)
{
    char title[256];
    void **args = (void **)lp;

    if (!IsWindowVisible(hwnd) || !GetWindowTextA(hwnd, title, sizeof(title))) return TRUE;
    if (!strstr(title, args[0])) return TRUE;
    args[1] = hwnd;
    return FALSE;
}

static HWND find_window(const char *title)
{
    void *args[2] = { (void *)title, NULL };
    EnumWindows(find_cb, (LPARAM)args);
    return args[1];
}

static BOOL CALLBACK monitor_cb(HMONITOR monitor, HDC dc, RECT *rect, LPARAM lp)
{
    MONITORINFOEXA mi = { .cbSize = sizeof(mi) };

    GetMonitorInfoA(monitor, (MONITORINFO *)&mi);
    printf("monitor %s flags %lx (%ld,%ld)-(%ld,%ld) work (%ld,%ld)-(%ld,%ld)\n", mi.szDevice, mi.dwFlags,
           mi.rcMonitor.left, mi.rcMonitor.top, mi.rcMonitor.right, mi.rcMonitor.bottom,
           mi.rcWork.left, mi.rcWork.top, mi.rcWork.right, mi.rcWork.bottom);
    return TRUE;
}

static void list_modes(void)
{
    DISPLAY_DEVICEA dev = { .cb = sizeof(dev) };

    for (int i = 0; EnumDisplayDevicesA(NULL, i, &dev, 0); i++)
    {
        DEVMODEA dm = { .dmSize = sizeof(dm) };
        int count = 0;

        if (!(dev.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP)) continue;
        printf("%s\n", dev.DeviceName);
        for (int j = 0; EnumDisplaySettingsA(dev.DeviceName, j, &dm); j++, count++)
            printf("    %lux%lu @%lu\n", dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency);
        printf("    (%d modes total)\n", count);
    }
}

static void send_key(WORD vk, BOOL up)
{
    INPUT input = { .type = INPUT_KEYBOARD, .ki = { .wVk = vk, .dwFlags = up ? KEYEVENTF_KEYUP : 0 } };
    SendInput(1, &input, sizeof(input));
    Sleep(30);
}

static void key_with_modifier(WORD modifier, WORD vk)
{
    if (modifier) send_key(modifier, FALSE);
    send_key(vk, FALSE);
    send_key(vk, TRUE);
    if (modifier) send_key(modifier, TRUE);
}

int main(int argc, char **argv)
{
    const char *cmd = argc > 1 ? argv[1] : "";

    SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);

    if (!strcmp(cmd, "list")) EnumWindows(list_cb, 0);
    else if (!strcmp(cmd, "children") && argc > 2)
    {
        HWND hwnd = find_window(argv[2]);
        if (!hwnd) { printf("no window '%s'\n", argv[2]); return 1; }
        print_window(hwnd, 0);
        list_children(hwnd, 1);
    }
    else if (!strcmp(cmd, "monitors"))
    {
        printf("virtual (%d,%d) %dx%d primary %dx%d\n", GetSystemMetrics(SM_XVIRTUALSCREEN), GetSystemMetrics(SM_YVIRTUALSCREEN),
               GetSystemMetrics(SM_CXVIRTUALSCREEN), GetSystemMetrics(SM_CYVIRTUALSCREEN),
               GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));
        EnumDisplayMonitors(NULL, NULL, monitor_cb, 0);
    }
    else if (!strcmp(cmd, "modes")) list_modes();
    else if (!strcmp(cmd, "click") && argc > 3)
    {
        SetCursorPos(atoi(argv[2]), atoi(argv[3]));
        Sleep(100);
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
    }
    else if (!strcmp(cmd, "vk") && argc > 2) key_with_modifier(0, atoi(argv[2]));
    else if (!strcmp(cmd, "ctrlvk") && argc > 2) key_with_modifier(VK_CONTROL, atoi(argv[2]));
    else if (!strcmp(cmd, "shiftvk") && argc > 2) key_with_modifier(VK_SHIFT, atoi(argv[2]));
    else if (!strcmp(cmd, "redraw") && argc > 2)
    {
        HWND hwnd = find_window(argv[2]);
        if (!hwnd) { printf("no window '%s'\n", argv[2]); return 1; }
        RedrawWindow(hwnd, NULL, NULL, RDW_INVALIDATE | RDW_ERASE | RDW_FRAME | RDW_ALLCHILDREN | RDW_UPDATENOW);
    }
    else
    {
        printf("usage: wtool list | children <title> | monitors | modes | click <x> <y> |\n"
               "             vk <code> | ctrlvk <code> | shiftvk <code> | redraw <title>\n"
               "coordinates are raw (per-monitor aware) screen pixels\n");
        return 1;
    }
    return 0;
}

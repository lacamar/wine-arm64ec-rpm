#include <windows.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    POINT pos;

    if (argc < 3) { printf("usage: wclick <raw x> <raw y> [right]\n"); return 1; }
    SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
    SetCursorPos(atoi(argv[1]), atoi(argv[2]));
    Sleep(100);
    if (argc > 3 && !strcmp(argv[3], "right"))
    {
        mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0); Sleep(60);
        mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0);
    }
    else
    {
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
    }
    Sleep(100);
    GetCursorPos(&pos);
    printf("cursor now (%ld,%ld)\n", pos.x, pos.y);
    return 0;
}

OUT ?= $(or $(XDG_CACHE_HOME),$(HOME)/.cache)/wine-arm64ec-dev/tools
CC32 = i686-w64-mingw32-gcc
CC64 = x86_64-w64-mingw32-gcc
CFLAGS = -O1 -Wall

WIN32 = smctest suspendtest tsospin winrect wclick wtool fxtest cbjittest
WIN64 = suspendtest tsospin winrect
SCRIPTS = dumpstack.py wkill.sh wshot.sh

all: $(WIN32:%=$(OUT)/%32.exe) $(WIN64:%=$(OUT)/%64.exe) $(OUT)/prtest $(SCRIPTS:%=$(OUT)/%)

$(OUT):
	mkdir -p $@

# self-modifying code must not be folded or reordered
$(OUT)/smctest32.exe: smctest.c | $(OUT)
	$(CC32) -O0 -Wall -o $@ $<

$(OUT)/fxtest32.exe: fxtest.c | $(OUT)
	$(CC32) $(CFLAGS) -o $@ $< -ld3d9

$(OUT)/%32.exe: %.c | $(OUT)
	$(CC32) $(CFLAGS) -o $@ $< -luser32 -lgdi32

$(OUT)/%64.exe: %.c | $(OUT)
	$(CC64) $(CFLAGS) -o $@ $< -luser32 -lgdi32

$(OUT)/prtest: prtest.c | $(OUT)
	$(CC) $(CFLAGS) -o $@ $<

$(OUT)/%: % | $(OUT)
	install -m 755 $< $@

clean:
	rm -rf $(OUT)

.PHONY: all clean

OUT ?= $(or $(XDG_CACHE_HOME),$(HOME)/.cache)/wine-arm64ec-dev/tools
CC32 = i686-w64-mingw32-gcc
CC64 = x86_64-w64-mingw32-gcc
CFLAGS = -O1 -Wall

WIN32 = smctest suspendtest tsospin winrect wclick wtool fxtest cbjittest memtest sehtest poptest divtest
WIN64 = suspendtest tsospin winrect memtest sehtest poptest divtest
SCRIPTS = dumpstack.py wkill.sh wshot.sh

all: $(WIN32:%=$(OUT)/%32.exe) $(WIN64:%=$(OUT)/%64.exe) $(OUT)/shtest32.exe $(OUT)/shtest64.exe \
     $(OUT)/shdll32.dll $(OUT)/shdll64.dll $(OUT)/prtest $(SCRIPTS:%=$(OUT)/%)

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

$(OUT)/shdll32.dll: shdll.c | $(OUT)
	$(CC32) $(CFLAGS) -shared -o $@ $<

$(OUT)/shdll64.dll: shdll.c | $(OUT)
	$(CC64) $(CFLAGS) -shared -o $@ $<

$(OUT)/prtest: prtest.c | $(OUT)
	$(CC) $(CFLAGS) -o $@ $<

$(OUT)/%: % | $(OUT)
	install -m 755 $< $@

clean:
	rm -rf $(OUT)

.PHONY: all clean

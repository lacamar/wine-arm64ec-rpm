#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

static unsigned long long rng = 0x9e3779b97f4a7c15ull;

static unsigned long long next(void)
{
    rng ^= rng << 13;
    rng ^= rng >> 7;
    rng ^= rng << 17;
    return rng;
}

/* verify each quotient/remainder with multiplication only, so a broken divide can't vouch for itself */
#define CHECK(type, a, b, name) do { \
    type q_ = (a) / (b), r_ = (a) % (b); \
    if ((type)(q_ * (b) + r_) != (a)) { printf("%s: %lld / %lld = %lld r %lld\n", name, (long long)(a), (long long)(b), (long long)q_, (long long)r_); fails++; } \
} while (0)

static volatile unsigned int g_u32;
static volatile int g_s32;
static volatile unsigned long long g_u64;
static volatile long long g_s64;

int main(int argc, char **argv)
{
    int i, fails = 0, rounds = argc > 1 ? atoi(argv[1]) : 2000000;

    for (i = 0; i < rounds; i++)
    {
        unsigned long long x = next(), y = next() | 1;
        unsigned int ux = (unsigned int)x, uy = (unsigned int)(y >> (i & 31)) | 1;
        int sx = (int)x, sy = (int)(y >> (i & 31)) | 1;
        unsigned short hx = (unsigned short)x, hy = (unsigned short)(y >> (i & 15)) | 1;
        unsigned char bx = (unsigned char)x, by = (unsigned char)(y >> (i & 7)) | 1;
        long long lx = (long long)x, ly = (long long)(y >> (i & 63)) | 1;

        CHECK(unsigned int, ux, uy, "div32");
        CHECK(int, sx, sy, "idiv32");
        CHECK(unsigned short, hx, hy, "div16");
        CHECK(unsigned char, bx, by, "div8");
        CHECK(unsigned long long, x, y >> (i & 63) | 1, "div64");
        CHECK(long long, lx, ly, "idiv64");
        /* divisors in memory: div/idiv with a memory operand */
        g_u32 = uy; g_s32 = sy; g_u64 = y >> (i & 63) | 1; g_s64 = ly;
        { unsigned int q = ux / g_u32, r = ux % g_u32; if (q * g_u32 + r != ux) { printf("mdiv32\n"); fails++; } }
        { int q = sx / g_s32, r = sx % g_s32; if (q * g_s32 + r != sx) { printf("midiv32\n"); fails++; } }
        { unsigned long long q = x / g_u64, r = x % g_u64; if (q * g_u64 + r != x) { printf("mdiv64\n"); fails++; } }
        { long long q = lx / g_s64, r = lx % g_s64; if (q * g_s64 + r != lx) { printf("midiv64\n"); fails++; } }
        if (fails > 20) break;
    }
    printf("%d-bit divtest: %d failures in %d rounds\n", (int)sizeof(void *) * 8, fails, i);
    return fails != 0;
}

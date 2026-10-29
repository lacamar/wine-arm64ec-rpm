#!/bin/bash
set -e
for d; do
  cd "/src/arch/$d"
  makepkg -Csfi --noconfirm --needed
done

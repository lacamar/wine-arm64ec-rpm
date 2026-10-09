#!/bin/bash
set -e
for d; do
  cd "/src/arch/$d"
  updpkgsums
  makepkg -Csfi --noconfirm --needed
done

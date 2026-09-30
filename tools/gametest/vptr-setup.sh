#!/usr/bin/env bash
# vptr-setup.sh  generate the pywayland bindings vptr.py needs (pointer + keyboard), next to it
cd "$(dirname "$0")" && python3 -m pywayland.scanner -i /usr/share/wayland/wayland.xml wlr-virtual-pointer-unstable-v1.xml virtual-keyboard-unstable-v1.xml -o proto && touch proto/__init__.py

#!/usr/bin/env bash

# selenium-driverless is unfree

#cd "$(dirname "$0")"
d="$(dirname "$0")"

#NIXPKGS_ALLOW_UNFREE=1 nix-shell
NIXPKGS_ALLOW_UNFREE=1 nix-shell $d/shell.nix

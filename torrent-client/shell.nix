{ pkgs ? import <nixpkgs> {} }:

with pkgs;

let
#  bcoding = python3.pkgs.callPackage ./bcoding.nix {};
#  pubsub = python3.pkgs.callPackage ./pubsub.nix {};
in

mkShell {

buildInputs = [
  python3
] ++ (with python3.pkgs; [

/*
bcoding # ==1.5
bitstring # == 3.1.7
pypubsub # == 4.0.3
requests # >= 2.24.0
pubsub # == 0.1.2
#ipaddress # == 1.0.23 # error: ipaddress has been removed because it is no longer required since python 2.7.
*/

  python3.pkgs.libtorrent-rasterbar

]);

}

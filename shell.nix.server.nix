{
  pkgs ? import <nixpkgs> {}
}:

let
  extraPythonPackages = rec {
    stream-zip = pkgs.python3.pkgs.callPackage ./nix/stream-zip.nix { };
  };
  python = pkgs.python3.withPackages (pythonPackages:
  (with pythonPackages; [
    guessit # parse video filenames
    langcodes
    charset-normalizer
  ])
  ++
  (with extraPythonPackages; [
    stream-zip
  ])
  );
in

pkgs.mkShell rec {
  buildInputs = (with pkgs; [
    lighttpd
  ]) ++ [
    python
  ]
  ++
  (with extraPythonPackages; [
    stream-zip
  ]);
}

{
  pkgs ? import <nixpkgs> {}
  #pkgs ? import ./. {}
}:

let
  # nix-init ./nix/pyppeteer-stealth.nix --url https://pypi.org/project/pyppeteer-stealth/
  # HTTP 404
  # expected https://files.pythonhosted.org/packages/f8/64/ae51d6c88406ab8a685b0c83af9fc6ef4275982f391258d9167ddde88cf1/pyppeteer_stealth-2.7.4.tar.gz
  # actual https://pypi.org/packages/source/p/pyppeteer-stealth/pyppeteer-stealth-2.7.4.tar.gz
  extraPythonPackages = {
    pyppeteer-stealth = pkgs.python3.pkgs.callPackage ./nix/pyppeteer-stealth.nix {};
    playwright-stealth = pkgs.python3.pkgs.callPackage ./nix/playwright-stealth.nix {};
    undetected-playwright = pkgs.python3.pkgs.callPackage ./nix/undetected-playwright.nix {};
    pygnuutils = pkgs.python3.pkgs.callPackage ./nix/pygnuutils.nix {};
  };

  python = pkgs.python3.withPackages (pp: with pp; [
    requests
    magic # libmagic
    #extraPythonPackages.pygnuutils # GNU version sort
    playwright
    #extraPythonPackages.playwright-stealth # FIXME not found
    #extraPythonPackages.pyppeteer-stealth # FIXME not found
    #extraPythonPackages.undetected-playwright # FIXME not found
    setuptools # pkg_resources for playwright-stealth
    #pyppeteer pyppeteer-stealth # puppeteer # old
    kaitaistruct
    sqlglot
  ]);

  # building sqlite took about 15 minutes on my laptop
  sqlite-debug = (pkgs.sqlite.overrideAttrs (oldAttrs: {
#    src = ./sqlite;
    NIX_CFLAGS_COMPILE = oldAttrs.NIX_CFLAGS_COMPILE + " " + (toString [
# https://sqlite.org/debugging.html
# https://sqlite.org/compile.html
"-DSQLITE_DEBUG=1" # enable assert() statements (run 3x slower), enable debugging of the Virtual Machine
"-DSQLITE_ENABLE_EXPLAIN_COMMENTS=1" # add comment text to the output of EXPLAIN
"-DSQLITE_ENABLE_TREETRACE=1" # .treetrace: trace SELECT and DML statements # not working?
"-DSQLITE_ENABLE_WHERETRACE=1" # .wheretrace: trace WHERE clauses
"-DSQLITE_ENABLE_IOTRACE=1" # .iotrace: low-level log of I/O activity
"-DSQLITE_ENABLE_OFFSET_SQL_FUNC=1" # sqlite_offset(X): get offset in database file
    ]);
  }));

in

pkgs.mkShell rec {

  PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright.browsers}";

  #CHROME_BIN = "${pkgs.chromium.outPath}/bin/chromium";

  # https://github.com/justinwoo/my-blog-posts/blob/master/posts/2019-08-23-using-puppeteer-with-node2nix.md
  # https://github.com/puppeteer/puppeteer/issues/244 # Method to skip installing Chromium
  PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "1";
  PUPPETEER_EXECUTABLE_PATH = "${pkgs.chromium.outPath}/bin/chromium";

  PYPPETEER_SKIP_CHROMIUM_DOWNLOAD = PUPPETEER_SKIP_CHROMIUM_DOWNLOAD;
  PYPPETEER_EXECUTABLE_PATH = PUPPETEER_EXECUTABLE_PATH;

buildInputs = (with pkgs; [
  #gnumake
  #playwright
  squashfsTools # mksquashfs
]) ++ [
  python
  sqlite-debug
  #extraPythonPackages.playwright-stealth
  extraPythonPackages.pygnuutils
  extraPythonPackages.pyppeteer-stealth
  extraPythonPackages.undetected-playwright
];

}

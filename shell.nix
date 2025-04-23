{
  pkgs ? import <nixpkgs> {}
  #pkgs ? import ./. {}
}:

let
  # nix-init ./nix/pyppeteer-stealth.nix --url https://pypi.org/project/pyppeteer-stealth/
  # HTTP 404
  # expected https://files.pythonhosted.org/packages/f8/64/ae51d6c88406ab8a685b0c83af9fc6ef4275982f391258d9167ddde88cf1/pyppeteer_stealth-2.7.4.tar.gz
  # actual https://pypi.org/packages/source/p/pyppeteer-stealth/pyppeteer-stealth-2.7.4.tar.gz
  extraPythonPackages = rec {
    #pyppeteer-stealth = pkgs.python3.pkgs.callPackage ./nix/pyppeteer-stealth.nix {};
    #playwright-stealth = pkgs.python3.pkgs.callPackage ./nix/playwright-stealth.nix {};
    #undetected-playwright = pkgs.python3.pkgs.callPackage ./nix/undetected-playwright.nix {};
    #pygnuutils = pkgs.python3.pkgs.callPackage ./nix/pygnuutils.nix {};
    #pycdlib = pkgs.python3.pkgs.callPackage ./nix/pycdlib.nix {};
    chromecontroller = pkgs.python3.pkgs.callPackage ./nix/chromecontroller.nix {};
    browser-debugger-tools = pkgs.python3.pkgs.callPackage ./nix/browser-debugger-tools.nix {};
    pychrome = pkgs.python3.pkgs.callPackage ./nix/pychrome.nix {};
    pychromedevtools = pkgs.python3.pkgs.callPackage ./nix/pychromedevtools.nix {};
    cdp-socket = pkgs.python3.pkgs.callPackage ./nix/cdp-socket.nix {};
    # error: Package ‘python3.10-selenium-driverless-1.6.3.3’ has an unfree license (‘cc-by-nc-sa-40’), refusing to evaluate.
    selenium-driverless = pkgs.python3.pkgs.callPackage ./nix/selenium-driverless.nix {
      cdp-socket = pkgs.python3.pkgs.callPackage ./nix/cdp-socket.nix {};
      selenium = pkgs.python3.pkgs.callPackage ./nix/selenium.nix { };
    };
    stream-zip = pkgs.python3.pkgs.callPackage ./nix/stream-zip.nix { };
    # fix: ModuleNotFoundError: No module named 'selenium.webdriver.common.devtools'
    # https://github.com/milahu/nixpkgs/issues/20
    selenium = pkgs.python3.pkgs.callPackage ./nix/selenium.nix { };
    # undetected_chromedriver
    undetected-chromedriver = pkgs.python3.pkgs.callPackage ./nix/undetected-chromedriver.nix {
      # TODO scope
      pkgs-undetected-chromedriver = pkgs.callPackage ./nix/undetected-chromedriver-bin.nix {};
    };
    selenium-wire = pkgs.python3.pkgs.callPackage ./nix/selenium-wire.nix {
      # TODO scope
      inherit undetected-chromedriver;
    };
    flaresolverr = pkgs.python3.pkgs.callPackage ./nix/flaresolverr.nix {
      # TODO scope
      inherit undetected-chromedriver;
    };
    pysub-parser = pkgs.python3.pkgs.callPackage ./nix/pysub-parser.nix {};
    torf = pkgs.python3.pkgs.callPackage ./nix/torf.nix {
      flatbencode = pkgs.python3.pkgs.callPackage ./nix/flatbencode.nix {};
    };
  };

  #sqlite-bench = pkgs.callPackage ./nix/sqlite-bench.nix {};

  buster-client = pkgs.callPackage ./nix/buster-client.nix {};
  buster-client-setup = pkgs.callPackage ./nix/buster-client-setup.nix {
    buster-client = pkgs.callPackage ./nix/buster-client.nix {};
  };
  buster-client-setup-cli = pkgs.callPackage ./nix/buster-client-setup-cli.nix {
    buster-client = pkgs.callPackage ./nix/buster-client.nix {};
  };

  python = pkgs.python3.withPackages (pythonPackages:
  (with pythonPackages; [
    requests
    magic # libmagic
    chardet
    charset-normalizer
    guessit # parse video filenames
    langcodes
    #playwright
    setuptools # pkg_resources for playwright-stealth
    #pyppeteer pyppeteer-stealth # puppeteer # old
    #kaitaistruct
    #sqlglot
    # distributed processing
    # ray is too complex, has only binary package in nixpkgs https://github.com/NixOS/nixpkgs/pull/194357
    #ray
    # https://github.com/tomerfiliba-org/rpyc
    #rpyc
    aiohttp
    aiohttp-socks # https://stackoverflow.com/a/76656557/10440128
    aiohttp-retry
    aiodns # make aiohttp faster
    brotli # make aiohttp faster
    natsort
    #pycdlib
    psutil
    pyparsing
    cryptography
    nest-asyncio
    # FIXME passlib.exc.InternalBackendError: crypt.crypt() failed for unknown reason; passlib recommends running `pip install bcrypt` for general bcrypt support.(config=<hash <class 'str'> value omitted>, secret=<hash <class 'bytes'> value omitted>)
    #bcrypt
    # no. use patched version in lib/thirdparty/pysubs2
    #pysubs2
    lxml # xhtml parser
    beautifulsoup4 # html parser
    fritzconnection # fritzbox client
    #selenium
    praw # python reddit api wrapper
  ])
  ++
  (with extraPythonPackages; [
    #pygnuutils # GNU version sort
    #playwright-stealth # FIXME not found
    #pyppeteer-stealth # FIXME not found
    #undetected-playwright # FIXME not found
    #chromecontroller
    #browser-debugger-tools
    #pychrome
    #pychromedevtools
    selenium-driverless
    cdp-socket
    /*
    selenium-wire
    selenium
    flaresolverr
    undetected-chromedriver
    #pysub-parser
    */
    selenium
    stream-zip
    torf # torrent file
  ])
  );

  # building sqlite took about 15 minutes on my laptop
  sqlite-debug = (pkgs.sqlite.overrideAttrs (oldAttrs: {
    #src = ./sqlite;
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

  chromium = pkgs.ungoogled-chromium;

in

pkgs.mkShell rec {

  #PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright.browsers}";

  #CHROME_BIN = "${chromium.outPath}/bin/chromium";

  # https://github.com/justinwoo/my-blog-posts/blob/master/posts/2019-08-23-using-puppeteer-with-node2nix.md
  # https://github.com/puppeteer/puppeteer/issues/244 # Method to skip installing Chromium
  #PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "1";
  #PUPPETEER_EXECUTABLE_PATH = "${chromium.outPath}/bin/chromium";

  #PYPPETEER_SKIP_CHROMIUM_DOWNLOAD = PUPPETEER_SKIP_CHROMIUM_DOWNLOAD;
  #PYPPETEER_EXECUTABLE_PATH = PUPPETEER_EXECUTABLE_PATH;

  # used by flaresolverr, fetch-subs.py
  # https://github.com/FlareSolverr/FlareSolverr/pull/992

  /*
  CHROME_EXE_PATH = "${chromium}/bin/${chromium.meta.mainProgram}";
  PATCHED_DRIVER_PATH = "${extraPythonPackages.undetected-chromedriver.bin}/bin/chromedriver";
  PATCHED_DRIVER_IS_PATCHED = "1";
  */

  buildInputs = (with pkgs; [
    #gnumake
    #playwright
    #squashfsTools # mksquashfs
    /*
    sqlite
    udftools # mkudffs
    xorriso # xorrisofs
    #libfaketime # faketime # this was a desperate attempt at reproducible UDF images
    tigervnc # vnc server: Xvnc
    xcalib # invert colors: xcalib -i -a
    openssh # ssh client

    # https://en.wikipedia.org/wiki/Compositing_window_manager
    # compositing window managers are not lightweight
    # so we just use a compositor
    picom
    */

    /*
    # lightweight window managers
    icewm
    openbox
    tint2 # taskbar (for openbox etc)
    # https://wiki.archlinux.org/title/List_of_applications/Other#Taskbars
    awesome
    fluxbox
    spectrwm
    qtile
    #worm # error: undefined variable 'worm'
    dwm
    fvwm
    dmenu
    i3 xss-lock dex networkmanagerapplet i3status
    */

    /*
    # compressed filesystems
    erofs-utils
    squashfs-tools-ng

    # captcha solver
    # https://github.com/dessant/buster
    buster-client
    #buster-client-setup
    buster-client-setup-cli

    gost

    chromedriver # for selenium
    */

    chromium # for selenium

    # todo: replace with torf in python
    # fixme: build error
    #torrenttools

    lighttpd

  ]) ++ [
    python
    #sqlite-debug
    #sqlite-bench
  ]
  ++
  (with extraPythonPackages; [
    #playwright-stealth
    #pygnuutils
    #pyppeteer-stealth
    #undetected-playwright
    #pycdlib
    /*
    chromecontroller
    browser-debugger-tools
    pychrome
    pychromedevtools
    */
    selenium-driverless
    cdp-socket
    /*
    selenium-wire
    flaresolverr
    undetected-chromedriver
    chromium
    */
    #pysub-parser
    # fix: ModuleNotFoundError: No module named 'selenium.webdriver.common.devtools'
    selenium
    stream-zip
    torf # torrent file
  ]);

}

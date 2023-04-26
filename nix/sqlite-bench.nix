{ lib
, stdenv
, fetchFromGitHub
}:

stdenv.mkDerivation rec {
  pname = "sqlite-bench";
  version = "unstable-2022-09-16";

  src = fetchFromGitHub {
    owner = "ukontainer";
    repo = "sqlite-bench";
    rev = "78e6cdc3d8791c28730f35ba0bd527d34aed2af4";
    hash = "sha256-K7DgZtNweKq5cJo4+5IlpmuML3Ixd7geA/ihxDJlDOA=";
  };

  # fix: ld: cannot find -lpthread: No such file or directory
  # https://github.com/ukontainer/sqlite-bench/issues/10
  postPatch = ''
    substituteInPlace Makefile \
      --replace " -static" ""
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp sqlite-bench $out/bin
  '';

  meta = with lib; {
    description = "SQLite Benchmark";
    homepage = "https://github.com/ukontainer/sqlite-bench";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
  };
}

/*

wtf?

$ nix-build . -A python.pkgs.pysub-parser
this derivation will be built:
  /nix/store/4dvds5km5m590w23rkrbca49gcbwkbqv-python.10-pysub-parser-1.7.1.drv
error: getting status of '/nix/store/1cixhxcas898y246radrkjzyqp1z60m9-python-catch-conflicts-hook': No such file or directory

*/

{ lib
, python
, buildPythonPackage
, fetchFromGitHub
, poetry-core
, unidecode
}:

buildPythonPackage rec {
  pname = "pysub-parser";
  version = "1.7.1";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "fedecalendino";
    repo = "pysub-parser";
    rev = "v${version}";
    hash = "sha256-FwWkd+BGUtw+DrFUSYuCORV3PIKeryHrrAfuXcWUUqM=";
  };

  nativeBuildInputs = [
#    poetry-core
  ];

  propagatedBuildInputs = [
#    unidecode
  ];

  pythonImportsCheck = [ "pysubparser" ];

  meta = with lib; {
    description = "Library for extracting text and timestamps from multiple subtitle files (.ass, .ssa, .srt, .sub, .txt)";
    homepage = "https://github.com/fedecalendino/pysub-parser";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

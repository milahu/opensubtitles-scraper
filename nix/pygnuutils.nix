{ lib
, python3
, fetchPypi
, fetchFromGitHub
}:

python3.pkgs.buildPythonApplication rec {
  pname = "pygnuutils";
  version = "0.0.6";
  format = "setuptools";

  /*
  src = fetchPypi {
    inherit pname version;
    hash = "sha256-8whw8ZsfYg6/aR53QHKjdVmv53JrlLVN3S8hq0K4vkA=";
  };
  */

  # fix: FileNotFoundError: [Errno 2] No such file or directory: '/build/pygnuutils-0.0.6/requirements.txt'
  src = fetchFromGitHub {
    owner = "matan1008";
    repo = "pygnuutils";
    rev = "v${version}";
    hash = "sha256-4Nm8mBKhGuYxXs1hUQOSCd7+nSdptOwGUi+dMYh1p/8=";
  };

  propagatedBuildInputs = with python3.pkgs; [
    click
    #dataclasses # dataclasses will be included in Python 3.7
  ];

  checkInputs = with python3.pkgs; [
    pytest
  ];

  pythonImportsCheck = [ "pygnuutils" ];

  meta = with lib; {
    description = "A python implementation for GNU utils";
    homepage = "https://pypi.org/project/pygnuutils/";
    license = licenses.gpl3Only;
    maintainers = with maintainers; [ ];
  };
}

{ lib
, python
, fetchFromGitHub
}:

python.pkgs.buildPythonApplication rec {
  pname = "pycdlib";
  version = "1.14.0";
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "clalancette";
    repo = "pycdlib";
    rev = "v${version}";
    hash = "sha256-QZW9XhNp6gqwTJ0N2VKufQCfX67OoF/N8adQ+sLjc/4=";
  };

  pythonImportsCheck = [ "pycdlib" ];

  meta = with lib; {
    description = "Python library to read and write ISOs";
    homepage = "https://github.com/clalancette/pycdlib";
    changelog = "https://github.com/clalancette/pycdlib/blob/${src.rev}/CHANGELOG";
    license = licenses.lgpl21Only;
    maintainers = with maintainers; [ ];
  };
}

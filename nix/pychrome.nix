{ lib
, python
, fetchFromGitHub
}:

python.pkgs.buildPythonApplication rec {
  pname = "pychrome";
  version = "0.2.1";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "fate0";
    repo = "pychrome";
    rev = "v${version}";
    hash = "sha256-iZ7x0MTTVZd+J2c+6vZJzekHuK0Ae70JbFKPsNrq21o=";
  };

  nativeBuildInputs = [
    python.pkgs.setuptools
    python.pkgs.wheel
  ];

  propagatedBuildInputs = with python.pkgs; [
    websocket-client
    requests
    click
  ];

  pythonImportsCheck = [ "pychrome" ];

  meta = with lib; {
    description = "A Python Package for the Google Chrome Dev Protocol [threading base";
    homepage = "https://github.com/fate0/pychrome";
    license = licenses.bsd3;
    maintainers = with maintainers; [ ];
    mainProgram = "pychrome";
  };
}

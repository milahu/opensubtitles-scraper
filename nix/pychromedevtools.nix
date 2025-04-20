{ lib
, python
, fetchFromGitHub
}:

python.pkgs.buildPythonApplication rec {
  pname = "pychromedevtools";
  version = "1.0.2";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "marty90";
    repo = "PyChromeDevTools";
    rev = version;
    hash = "sha256-+cAH4iq+95mLjDQEaNnGR+jbVq230oihPXjbHKbd47k=";
  };

  nativeBuildInputs = [
    python.pkgs.setuptools
    python.pkgs.wheel
  ];

  propagatedBuildInputs = with python.pkgs; [
    requests
    websocket-client
  ];

  pythonImportsCheck = [ "PyChromeDevTools" ];

  meta = with lib; {
    description = "PyChromeDevTools is a python module that allows one to interact with Google Chrome using Chrome DevTools Protocol within a Python script";
    homepage = "https://github.com/marty90/PyChromeDevTools";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
    mainProgram = "py-chrome-dev-tools";
  };
}

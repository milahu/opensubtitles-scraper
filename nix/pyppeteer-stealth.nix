{ lib
, python3
, fetchPypi
}:

python3.pkgs.buildPythonApplication rec {
  pname = "pyppeteer-stealth";
  version = "2.7.4";
  format = "setuptools";

  src = fetchPypi {
    pname = "pyppeteer_stealth";
    inherit version;
    hash = "sha256-zR0EDyPxfHYmCkTH8pXiOBdKQcwoITzPhs95aljIpRQ=";
  };

  pythonImportsCheck = [ "pyppeteer_stealth" ];

  # TypeError: chrome_app() missing 1 required positional argument: 'page'
  doCheck = false;

  checkInputs = with python3.pkgs; [
    pyppeteer
  ];

  propagatedBuildInputs = with python3.pkgs; [
    pyppeteer
  ];

  meta = with lib; {
    description = "Pyppeteer stealth";
    homepage = "https://pypi.org/project/pyppeteer-stealth/";
    license = with licenses; [ ];
    maintainers = with maintainers; [ ];
  };
}

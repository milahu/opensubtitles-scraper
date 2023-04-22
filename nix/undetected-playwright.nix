{ lib
, python3
, fetchPypi
}:

python3.pkgs.buildPythonApplication rec {
  pname = "undetected-playwright";
  version = "0.0.5";
  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-V4I5VXVcesZdfB8VPXvMOV/EgvUIE9ViHk2cAL0pAF4=";
  };

  propagatedBuildInputs = with python3.pkgs; [
    playwright
  ];

  pythonImportsCheck = [ "undetected_playwright" ];

  meta = with lib; {
    description = "You know who I am";
    homepage = "https://pypi.org/project/undetected-playwright/";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
  };
}

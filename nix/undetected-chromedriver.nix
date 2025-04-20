{ lib
, fetchFromGitHub
, pkgs-undetected-chromedriver
# python.pkgs
, buildPythonApplication
, setuptools
, wheel
, requests
, certifi
, websockets
, selenium
}:

buildPythonApplication rec {
  pname = "undetected-chromedriver";
  # https://pypi.org/project/undetected-chromedriver/
  version = "3.5.4";
  pyproject = true;

  passthru = {
    # patched chromedriver binary
    # usage:
    /*
      undetected_chromedriver.Chrome(
        driver_executable_path="/path/to/chromedriver",
        driver_executable_is_patched=True,
      )
    */
    bin = pkgs-undetected-chromedriver;
  };

  src = fetchFromGitHub {
    /*
    owner = "ultrafunkamsterdam";
    repo = "undetected-chromedriver";
    rev = "783b8393157b578e19e85b04d300fe06efeef653";
    hash = "sha256-vQ66TAImX0GZCSIaphEfE9O/wMNflGuGB54+29FiUJE=";
    */
    # setup.py: import version
    # https://github.com/ultrafunkamsterdam/undetected-chromedriver/pull/1686
    # add parameter driver_executable_is_patched
    # https://github.com/ultrafunkamsterdam/undetected-chromedriver/pull/1687
    # add parameter: extra_chrome_arguments + dont set window size
    # https://github.com/ultrafunkamsterdam/undetected-chromedriver/pull/1692
    owner = "milahu";
    repo = "undetected-chromedriver";
    rev = "30120785db0072422aa240510a7d97919a74698e";
    hash = "sha256-TMukIVGM40Mq12IKfGePZPflZ+57WyV+3v0i0zLYpbM=";
  };

  nativeBuildInputs = [
    setuptools
    wheel
  ];

  propagatedBuildInputs = [
    requests
    certifi
    websockets
    selenium
  ];

  pythonImportsCheck = [ "undetected_chromedriver" ];

  meta = with lib; {
    description = "Custom Selenium Chromedriver | Zero-Config | Passes ALL bot mitigation systems (like Distil / Imperva/ Datadadome / CloudFlare IUAM";
    homepage = "https://github.com/ultrafunkamsterdam/undetected-chromedriver";
    license = licenses.gpl3Only;
    maintainers = with maintainers; [ ];
  };
}

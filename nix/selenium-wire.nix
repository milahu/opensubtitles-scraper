{ lib
, fetchFromGitHub
# python3.pkgs
, buildPythonPackage
, setuptools
, wheel
, undetected-chromedriver
, mitmproxy
}:

buildPythonPackage rec {
  pname = "selenium-wire";
  version = "5.1.0";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "wkeeling";
    repo = "selenium-wire";
    rev = version;
    hash = "sha256-KgaDxHS0dAK6CT53L1qqx1aORMmkeaiXAUtGC82hiIQ=";
  };

  nativeBuildInputs = [
    setuptools
    wheel
  ];

  propagatedBuildInputs = [
    # https://github.com/wkeeling/selenium-wire#bot-detection
    # https://github.com/wkeeling/selenium-wire/blob/master/seleniumwire/undetected_chromedriver/webdriver.py
    # selenium-wire will use our patched undetected_chromedriver
    # so it also accepts the parameter driver_executable_is_patched
    undetected-chromedriver
  ]
  ++
  # 27 deps for the bundled mitmproxy module
  mitmproxy.propagatedBuildInputs
  ;

  # the bundled mitmproxy module
  # seleniumwire/thirdparty/mitmproxy
  # is a patched version of
  # https://github.com/mitmproxy/mitmproxy
  # with the original mitmproxy module, this fails:
  # from mitmproxy import connections

  pythonImportsCheck = [ "seleniumwire" ];

  meta = with lib; {
    description = "Extends Selenium's Python bindings to give you the ability to inspect requests made by the browser";
    homepage = "https://github.com/wkeeling/selenium-wire";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

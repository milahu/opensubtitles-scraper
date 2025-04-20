{ lib
, python
, fetchPypi
, fetchFromGitHub
, playwright
, setuptools
, fetchpatch
}:

python.pkgs.buildPythonApplication rec {
  pname = "playwright-stealth";
  version = "1.0.5";
  format = "setuptools";

  # fix: better navigator.webdriver faking
  src = fetchFromGitHub {
    owner = "Mattwmaster58";
    repo = "playwright_stealth";
    rev = "448cbb59039e873de4d20ba77498d4f0d573d637";
    hash = "sha256-b3/beeuMPz9NCeAd6WkPYU3+3Zhe3LGhScDeawAy4Cw=";
  };

  propagatedBuildInputs = [
    setuptools # pkg_resources
  ];

  checkInputs = [
    playwright
  ];

  pythonImportsCheck = [ "playwright_stealth" ];

  meta = with lib; {
    description = "Playwright stealth";
    homepage = "https://pypi.org/project/playwright-stealth/";
    license = with licenses; [ ];
    maintainers = with maintainers; [ ];
  };

  # probably the pypi source is outdated
  # error: Hunk #1 FAILED at 31 (different line endings).
  /*
  src = fetchPypi {
    inherit pname version;
    hash = "sha256-KIOcwtqAOhVhYXmQB5IszGDoObtFx23yobQRRxv7G3o=";
  };
  patches = [
    # fix: better navigator.webdriver faking
    (fetchpatch {
      url = "https://github.com/AtuboDad/playwright_stealth/pull/15.patch";
      hash = "sha256-ePhqrVmDelYlOm7956VxQwuChrfUIu4b/X2RqPy6gDA=";
    })
  ];
  */
}

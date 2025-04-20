{ lib
, python
, fetchFromGitHub
}:

python.pkgs.buildPythonPackage rec {
  pname = "stream-zip";
  version = "0.0.71";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "uktrade";
    repo = "stream-zip";
    rev = "v${version}";
    hash = "sha256-zcYfpojAy0ZfJHuvYtsEr9SSpTc+tOH8gTKI9Fd4oHg=";
  };

  nativeBuildInputs = [
    python.pkgs.hatchling
  ];

  propagatedBuildInputs = with python.pkgs; [
    pycryptodome
  ];

  passthru.optional-dependencies = with python.pkgs; {
    ci = [
      coverage
      pycryptodome
      pytest
      pytest-cov
      pyzipper
      stream-unzip
    ];
    dev = [
      coverage
      pytest
      pytest-cov
      pyzipper
      stream-unzip
    ];
  };

  pythonImportsCheck = [ "stream_zip" ];

  meta = with lib; {
    description = "Python function to construct a ZIP archive on the fly";
    homepage = "https://github.com/uktrade/stream-zip";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}

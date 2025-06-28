{ lib
, python
, fetchFromGitHub
, fetchurl
}:

python.pkgs.buildPythonPackage rec {
  pname = "stream-zip";
  version = "0.0.81";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "milahu";
    repo = "stream-zip";
    rev = "v${version}";
    hash = "sha256-kSRCl0mVgntC53cCB6u5OAkzFk+a9yoyfiUJH8yLqAI=";
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

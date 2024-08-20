final: prev: rec {
  python3 = prev.python3.override {
    packageOverrides = final: prev:
      {
        univers = python3Packages.callPackage
          ({ lib
           , buildPythonPackage
           , git
           , setuptools-scm
           , attrs
           , packaging
           , pyparsing
           , semantic-version
           , semver
           , black
           , commoncode
           , pytestCheckHook
           , saneyaml
           }: buildPythonPackage rec {
            name = "univers";

            src = ./.;

            nativeBuildInputs = [ git setuptools-scm ];
            propagatedBuildInputs = [ attrs packaging pyparsing semantic-version semver ];
            checkInputs = [ black commoncode pytestCheckHook saneyaml ];

            dontConfigure = true; # ./configure tries to setup virtualenv and downloads dependencies

            pythonImportsCheck = [ "univers" ];

            meta = with lib; {
              description = "Library for parsing version ranges and expressions";
              homepage = "https://github.com/aboutcode-org/univers";
              license = with licenses; [ asl20 bsd3 mit ];
            };
          })
          { };
      };
  };
  python3Packages = prev.recurseIntoAttrs python3.pkgs;
}

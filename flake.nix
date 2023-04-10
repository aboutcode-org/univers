{
  description = "Parse and compare all the package versions and all the ranges. From debian, npm, pypi, ruby and more. Process all the version range specs and expressions.";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: ({
    overlays.default = import ./overlay.nix;
  }) // (
    let
      supportedSystems = [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
      nixpkgsFor = forAllSystems (system: self.overlays.default null nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (system: rec {
        python3Packages = {
          inherit (nixpkgsFor.${system}.python3Packages) univers;
        };
        default = python3Packages.univers;
      });
    }
  );
}

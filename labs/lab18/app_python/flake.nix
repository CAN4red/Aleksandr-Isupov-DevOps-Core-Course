{
  description = "DevOps Info Service - Reproducible Build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }:
    let
      # System configuration - adjust for your platform:
      # - x86_64-linux: Linux (Intel/AMD), WSL2
      # - aarch64-linux: Linux (ARM64)
      # - x86_64-darwin: macOS Intel
      # - aarch64-darwin: macOS Apple Silicon (M1/M2/M3)
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # Development shell with all dependencies
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.flask
        ];
      };
    };
}

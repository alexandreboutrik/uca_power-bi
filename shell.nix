{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    pandas
    numpy
    scipy
    statsmodels
    matplotlib
    seaborn
    scikit-learn
    jupyter
	geopandas
	shapely
  ]);
in pkgs.mkShell {
  packages = [
    pythonEnv
  ];

  shellHook = ''
    echo "=================================================="
    echo "🐍 Python Data Science Environment Loaded."
    echo "Packages available: pandas, numpy, scipy, statsmodels, scikit-learn, etc."
    python --version
    echo "=================================================="
  '';
}

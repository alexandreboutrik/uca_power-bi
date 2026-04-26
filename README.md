<div align="center">

<h1 align="center">UCA Power BI</h1>

<div align="center">
<img src="https://img.shields.io/badge/tool-Power_BI-C59B00">
<img src="https://img.shields.io/badge/language-Python-3776AB">
</div>

<p align="center">
  <a href="#description">Description</a> •
  <a href="#file-tree-structure">File Tree Structure</a> •
  <a href="#ready-to-use-datasets">Ready to Use Datasets</a> •
  <a href="#raw-datasets">Raw Datasets</a> •
  <a href="#scripts-overview">Scripts Overview</a>
</p>

---

</div>

## Description

This repository contains the data processing pipeline developed for our university assignment utilizing Power BI. The project is managed and executed by our working group consisting of Alexandre BOUTRIK, Mohamed Khalil RAHMOUNI, and Aziz LANDOULSI. 

> [!IMPORTANT]
> We are strictly prohibiting any alteration of the underlying dataset structure. We DO NOT remove, rename, or manipulate the core columns and their original values under any circumstances. Our methodology revolves exclusively around strategically filtering rows to construct smaller datasets targeting highly specific statistical niches for our Power BI visualizations.

## File Tree Structure

The repository architecture is organized to reflect the chronological processing lifecycle of our geographic datasets. The root directory houses a `data/raw/` folder containing the untouched compressed archives downloaded directly from the source. These archives are subsequently decompressed into the `data/extracted/` directory to expose the base CSV files.

We then use our filter script to reduce these massive files into temporary experimental outputs housed within the `data/processed/` directory. We then rename successful filtering sequences and transfer them to the `data/filtered/` directory to mark them as ready for PowerBI loading.

## Ready to Use Datasets (`data/filtered/`)

The following table catalogs the finalized datasets we have successfully filtered to highlight specific demographic trends for Power BI consumption.

| CSV Name | Line Count | Origin Dataset | Applied Filters |
|---|---|---|---|
| Dataset_Young_Families.csv | 3,295 | carreaux_nivNaturel_met.csv | log_ap90 > 30, men_5ind > 10, ind_0_3 > 20 |
| Dataset_Young_Alone_Apartments.csv | 21,274 | carreaux_nivNaturel_met.csv | ind_18_24 > 40, men_1ind > 30, men_coll > 20 |
| Dataset_Vulnerable_Zones.csv | 17,925 | carreaux_nivNaturel_met.csv | men_pauv > 20, log_soc > 30, men_fmp > 10 |
| Dataset_Urban_Density.csv | 27,841 | carreaux_nivNaturel_met.csv | ind > 500 |
| Dataset_Map_1km_Grids.csv | 58,162 | carreaux_nivNaturel_met.csv | tmaille = 1000 |

## Processed Datasets (`data/processed/` and `data/extracted/`)

* **Dataset Name**: `carreaux_nivNaturel_met.csv`
* **Institution**: INSEE
* **Extracted From**: `data/raw/Filosofi2019_carreaux_nivNaturel_csv.zip`
* **Description**: Revenus, pauvreté et niveau de vie - Données carroyées (FiLoSoFi)
* **Source URL**: https://www.data.gouv.fr/datasets/revenus-pauvrete-et-niveau-de-vie-donnees-carroyees
* **Last Update**: 2026-04-24
* **Downloaded On**: 2026-04-25

This dataset provides a view of demographics and living conditions across France using a grid system. Available variables (aka columns) are:

| Column Name | Description |
| --- | --- |
| **`idcar_nat`** | Identifiant Inspire du carreau de niveau naturel |
| **`tmaille`** | Taille en mètres du côté du carreau |
| **`ind`** | Nombre d'individus |
| **`men`** | Nombre de ménages |
| **`men_pauv`** | Nombre de ménages pauvres |
| **`men_1ind`** | Nombre de ménages d'un seul individu |
| **`men_5ind`** | Nombre de ménages de 5 individus ou plus |
| **`men_prop`** | Nombre de ménages propriétaires |
| **`men_fmp`** | Nombre de ménages monoparentaux |
| **`ind_snv`** | Somme des niveaux de vie winsorisés des individus |
| **`men_surf`** | Somme de la surface des logements du carreau |
| **`men_coll`** | Nombre de ménages en logements collectifs |
| **`men_mais`** | Nombre de ménages en maison |
| **`log_av45`** | Nombre de logements construits avant 1945 |
| **`log_45_70`** | Nombre de logements construits entre 1945 et 1969 |
| **`log_70_90`** | Nombre de logements construits entre 1970 et 1989 |
| **`log_ap90`** | Nombre de logements construits depuis 1990 |
| **`log_inc`** | Nombre de logements dont la date de construction est inconnue |
| **`log_soc`** | Nombre de logements sociaux |
| **`ind_0_3`** | Nombre d'individus de 0 à 3 ans |
| **`ind_4_5`** | Nombre d'individus de 4 à 5 ans |
| **`ind_6_10`** | Nombre d'individus de 6 à 10 ans |
| **`ind_11_17`** | Nombre d'individus de 11 à 17 ans |
| **`ind_18_24`** | Nombre d'individus de 18 à 24 ans |
| **`ind_25_39`** | Nombre d'individus de 25 à 39 ans |
| **`ind_40_54`** | Nombre d'individus de 40 à 54 ans |
| **`ind_55_64`** | Nombre d'individus de 55 à 64 ans |
| **`ind_65_79`** | Nombre d'individus de 65 à 79 ans |
| **`ind_80p`** | Nombre d'individus de 80 ans ou plus |
| **`ind_inc`** | Nombre d'individus dont l'âge est inconnu |

## Raw Datasets (`data/raw/`)

* **Dataset Name**: Filosofi2019_carreaux_nivNaturel_csv.zip
  * **Source URL**: https://www.insee.fr/fr/statistiques/7655503?sommaire=7655515
  * **Download Date**: 2026-04-25
  * **Files Extracted**: `data/extracted/carreaux_nivNaturel_mart.csv`, `data/extracted/carreaux_nivNaturel_met.csv`, `data/extracted/carreaux_nivNaturel_reun.csv`
  * **SHA256 Checksum**: `08e0976007f76b813e00b05795b9f9020635724eac5977ddabab1b8944aa9a87`

* **Dataset Name**: cantons-version-simplifiee.geojson
  * **Source URL**: https://github.com/gregoiredavid/france-geojson
  * **Download Date**: 2026-04-26
  * **Usage**: This geographic boundaries file is utilized by the `scripts/map_grids.py` script to perform spatial joins mapping our grid data to respective cantons (more information is available in the **Scripts Overview** section).

## Scripts Overview

Our data transformation pipeline relies on a suite of custom Python and Bash.

The extraction script (`scripts/extract_data.sh`) automates the unzipping of raw archives and securely registers their metadata into our configuration tracking system.

The exploration utility (`scripts/explore_data.py`) programmatically reads headers from unknown CSV files to expose a clear summary of available variables without crashing.

The dataset filter (`scripts/filter_dataset.py`) acts as the core engine by streaming massive files in memory chunks to keep matching rows and discard irrelevant data based on numerical thresholds.

The grid mapping script (`scripts/map_grids.py`) applies a spatial join to mathematically calculate the exact geographic canton of each data point. Because our foundational data utilizes the standard European Inspire grid format (where coordinates are encoded directly into strings like `CRS3035RES1000mN2032000E4250000`), the script first parses out the exact North and East coordinates to pinpoint the grid's center. These spatial points are then evaluated against the geographic multipolygon boundaries provided by our `cantons-version-simplifiee.geojson` dataset (sourced externally from Gregoire David's France GeoJSON repository) to successfully pin our demographic data to recognized administrative regions.

# NHST vs Bayes Factor

This repository contains the experiments for "Le Maguer, Sébastien, Nelly Barbot, and Sofoklis Kakouros. "Bayesian Insights into Speech Synthesis Evaluation." Spoken Language Technology Workshop. IEEE, 2026."

A few notes:
  - The entry point is `run.sh`. Please refer to it to understand the process
  - Some tests (shapiro, t-test) are here for checking potential issues. We know they are not valid, but the goal is to determine if we arrive to different conclusions
  - Bayesics & dfba are both used because the idiot who started the repo is not really clear on which one to use yet - but he is still aware that bayesics relies on dfba :D

## How to install

You first need to install conda/mamba/micromamba and the run:

```sh
conda env create -f env.yaml
```

Activate the environment:
```sh
conda activate bayes_nhst
```

Install the R packages which are not available on conda:

```sh
Rscript --vanilla install_packages.R
```

## How to run
First activate the environment, and then run:

```sh
bash -xe run.sh
```

If you are generating the data for the overleaf project, please use the following command:

```sh
ROOT_OUTPUT_DIR=<overleaf_git_root_dir>/assets/ bash -xe run.sh
```

You will then just have to stage, commit and push the changes to the overleaf project for them to be taken into account during the compilation of the paper.

## Results

All the results are saved into the directory `output`.
For now, we consider two type of files:
  - *.tsv :: corresponds to the dataframe containing all the raw results (the basename indicates the statistical tool used)
  - *.pdf :: corresponds to decision matrix according to different thresholds (the basename indicates the statistical tool used). By threshold I mean the \alpha for the p-value & the condition for the BF10. Shapiro & bayesics are ignored for this.

## References
- Blizzard 2025 data :: Do, P., Coler, M., Dijkstra, J., Marchenko, I., Verkhodanova, V., Le Maguer, S. (2025) The Blizzard Challenge 2025. Proc. The Blizzard Challenge 2025, 1-17, doi: 10.21437/Blizzard.2025-1
- MUSHRA/Ranking for Blizzard 2013 :: Le Maguer, S., Šimko, J. (2025) Speech Synthesis Evaluation from a voting perspective - a starting point. Proc. 13th edition of the Speech Synthesis Workshop, 123-129, doi: 10.21437/SSW.2025-19

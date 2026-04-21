#!/bin/python
import sys
import pathlib
import subprocess

OUTPUT_DIR= pathlib.Path(sys.argv[2])

with open(sys.argv[1], "r") as f_list:
    expes = f_list.readlines()

# A bit dirty : Ignore header and generate list elements => /!\ order
expes = expes[1:]
expes = [e.strip().split("\t") for e in expes]

for dataset_df_file, cur_exp, score_name, with_audio, with_step in expes:
    if dataset_df_file.startswith("#"):
        continue

    with_audio = with_audio.lower() == "true"
    with_step = with_step.lower() == "true"
    exp_output_dir = OUTPUT_DIR/score_name/cur_exp
    exp_output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "Rscript", "--vanilla", "scripts/expe_analysis.R",
        # "-B", # NOTE: for SLT, we disabled bonf.
        "-e", cur_exp,
        "-s", score_name,
        "-i", dataset_df_file,
        "-d", exp_output_dir/"dfba.tsv",
        "-b", exp_output_dir/"bayesics.tsv",
        "-w", exp_output_dir/"wilcoxon.tsv",
        "-n", exp_output_dir/"shapiro.tsv",
        "-o", exp_output_dir/"statistics.tsv",
        "-t", exp_output_dir/"ttest.tsv",
        "--plot_output_dir", exp_output_dir/"dfba",
        "--plot_output_bayesics_dir", exp_output_dir/"bayesics",
    ]
    if with_audio:
        cmd.append("-A")
    if with_step:
        cmd.append("-S")

    print(f"[Run] {' '.join([str(e) for e in cmd])}")
    subprocess.run(cmd)

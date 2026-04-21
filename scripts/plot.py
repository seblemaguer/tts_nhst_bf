#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <sebastien.lemaguer@helsinki.fi>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 16 kesäkuu 2026
"""

# Core Python
import argparse
import sys
import pathlib

# Data processing
import numpy as np
import numpy.typing as npt
import pandas as pd

# Plotting
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
font = {
    'family' : 'normal',
    #'weight' : 'bold',
    'size'   : 18
}

mpl.rc('font', **font)

# Messaging/logging
import logging
from logging.config import dictConfig

from latexfriendly import DICT_NAME2SHORTS
try:
    import pythonjsonlogger

    JSON_LOGGER = True
except Exception:
    JSON_LOGGER = False


###############################################################################
# global constants
###############################################################################
LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]
NUM_CATEGORIES = 5  # Number of categories (must match the number of color blocks - set to 5 to avoid recomp.)
DEFAULT_COLMAP_NAME = "viridis"


###############################################################################
# Functions
###############################################################################
def configure_logger(args) -> logging.Logger:
    """Setup the global logging configurations and instanciate a specific logger for the current script

    Parameters
    ----------
    args : dict
        The arguments given to the script

    Returns
    --------
    the logger: logger.Logger
    """
    # create logger and formatter
    logger = logging.getLogger()

    # Verbose level => logging level
    log_level = args.verbosity
    if args.verbosity >= len(LEVEL):
        log_level = len(LEVEL) - 1
        # logging.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)

    # Define the default logger configuration
    logging_config = dict(
        version=1,
        disable_existing_logger=True,
        formatters={
            "f": {
                "format": "[%(asctime)s] [%(levelname)s] — [%(name)s — %(funcName)s:%(lineno)d] %(message)s",
                "datefmt": "%d/%b/%Y: %H:%M:%S ",
            }
        },
        handlers={
            "h": {
                "class": "logging.StreamHandler",
                "formatter": "f",
                "level": LEVEL[log_level],
            }
        },
        root={"handlers": ["h"], "level": LEVEL[log_level]},
    )

    # Add file handler if file logging required
    if args.log_file is not None:
        cur_formatter_key = "f"
        if JSON_LOGGER:
            logging_config["formatters"]["j"] = {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(filename)s %(lineno)d %(message)s",
                "rename_fields": {"asctime": "time", "levelname": "level", "lineno": "line_number"},
            }
            cur_formatter_key = "j"

        logging_config["handlers"]["f"] = {
            "class": "logging.FileHandler",
            "formatter": cur_formatter_key,
            "level": LEVEL[log_level],
            "filename": args.log_file,
        }
        logging_config["root"]["handlers"] = ["h", "f"]

    # Setup logging configuration
    dictConfig(logging_config)

    # Retrieve and return the logger dedicated to the script
    logger = logging.getLogger(__name__)
    return logger


def define_argument_parser() -> argparse.ArgumentParser:
    """Defines the argument parser

    Returns
    --------
    The argument parser: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="")

    # Add logging options
    parser.add_argument("-l", "--log_file", default=None, help="Logger file")
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increase output verbosity",
    )

    # Add performative options
    parser.add_argument(
        "-c",
        "--cmap",
        default=DEFAULT_COLMAP_NAME,
        type=str,
        help=f"The name of the colormap used to extract the category colors [default={DEFAULT_COLMAP_NAME}]",
    )
    parser.add_argument("-s", "--scale", action="store_true", help="Apply scale in the statistics")

    # Add arguments
    parser.add_argument("expes", help="The list of experiments to plot (names are comma separated)")
    parser.add_argument("tools", help="The list of statistical tools to plot (names are comma separated)")
    parser.add_argument("data_dir", help="The directory which contains the data to be plotted")
    parser.add_argument("plot_dir", help="The output directory which will contain the plots")

    # Return parser
    return parser


###############################################################################
# Helpers
###############################################################################
def generate_shared_palette(cmap_name: str, num_categories: int) -> npt.NDArray:
    """
    Samples a continuous colormap (e.g., viridis) at discrete intervals
    to create a fixed list of representative colors for categorical use.
    """
    # Get the colormap object
    cmap = plt.get_cmap(cmap_name)
    sampling_points = np.linspace(0, 1, num_categories)
    sampled_colors_rgba = cmap(sampling_points)

    return sampled_colors_rgba


def map_data_to_indices(raw_data):
    """Converts raw data into an integer index map."""
    index_map = np.zeros_like(raw_data, dtype=int)
    H, W = raw_data.shape
    h_step = H // NUM_CATEGORIES  # Size of each conceptual category band

    # Index mapping is fixed based on physical location:
    for i in range(NUM_CATEGORIES):
        start_row = i * h_step
        end_row = (i + 1) * h_step
        index_map[start_row:end_row, :] = i
    return index_map


###############################################################################
# Entry point
###############################################################################
def main():
    # Initialization of the argument parser and the logger
    arg_parser = define_argument_parser()
    args = arg_parser.parse_args()
    logger = configure_logger(args)

    # Process arguments
    expes = args.expes.split(",")
    tools = args.tools.split(",")
    data_dir = pathlib.Path(args.data_dir)
    plot_dir = pathlib.Path(args.plot_dir)
    plot_dir.mkdir(exist_ok=True, parents=True)

    # Generate color map
    color_list = generate_shared_palette(args.cmap, NUM_CATEGORIES)

    # Plot
    for tool in tools:
        input_root_file = data_dir / f"{tool}.tsv"
        df = pd.read_csv(input_root_file, sep="\t")

        df.replace(
            DICT_NAME2SHORTS,
            inplace=True,
        )

        # NOTE: everything is hacky here as thresholds have been hardcoded, and not fully clear about the BF10 management
        #       it would be good to check bayesics: https://github.com/dksewell/bayesics/blob/c2ddda91e5f0e4bc21f91d95363ab23d85f3f014/R/wilcoxon_test_b.R#L355
        if tool in ("dfba"):
            score = "evidence"
            df.loc[df.BF10 == np.inf, "BF10"] = 1000
            # df.loc[df.BF10 <1, "BF10"] = 1
            # Convert to two sided test
            df[score] = np.max([df.BF10, 1.0 / df.BF10], axis=0)
            if args.scale:
                bounds = [1, 3, 10, 30, 100, 1000]
                df.loc[df[score] > 100, score] = 200
                df.loc[(df[score] <= 100) & (df[score] > 30), score] = 55
                df.loc[(df[score] <= 30) & (df[score] > 10), score] = 15
                df.loc[(df[score] <= 10) & (df[score] > 3), score] = 5
                df.loc[(df[score] <= 3) & (df[score] > 1), score] = 2
                # df.loc[df[score] <= 1, score] = 0.5
            else:
                df.loc[df[score] > 1000, score] = 1000
                score_cmap = args.cmap
        elif tool in ("bayesics", "shapiro"):
            continue
        else:
            score = "p.value"
            if args.scale:
                bounds = [0, 0.001, 0.005, 0.01, 0.05, 1]
                df.loc[df[score] < 0.001, score] = 0.0003
                df.loc[(df[score] > 0.001) & (df[score] < 0.005), score] = 0.003
                df.loc[(df[score] > 0.005) & (df[score] < 0.01), score] = 0.006
                df.loc[(df[score] > 0.01) & (df[score] < 0.05), score] = 0.03
                df.loc[df[score] > 0.05, score] = 0.5
                color_list = color_list[::-1]
            else:
                df.loc[df[score] < 1e-6, score] = 1e-6
                score_cmap = f"{args.cmap}_r"

        if args.scale:
            score_cmap = ListedColormap(color_list)
            score_norm = mpl.colors.BoundaryNorm(bounds, score_cmap.N)
        else:
            score_norm = mpl.colors.LogNorm(vmin=df[score].min(), vmax=df[score].max())

        for cur_exp in expes:
            df_subset = df.loc[df.experiment == cur_exp, ["system_1", "system_2", score]]

            if df_subset.empty:
                logger.warning(f"{cur_exp} is not available in {data_dir}")
                continue
            else:
                logger.info(f"====== {cur_exp}/{tool} ======")
                logger.debug(df_subset)
            df_pivot = df_subset.pivot_table(index="system_1", columns="system_2", values=score)

            fig, ax = plt.subplots()

            # Ignore upper right triangle for readability puproposes
            for i in range(0, df_pivot.shape[0]):
                for j in range(i, df_pivot.shape[1]):
                    df_pivot.iloc[i, j] = pd.NA

            # show image
            im = ax.matshow(df_pivot.values, cmap=score_cmap, norm=score_norm)

            # make bar
            bar = plt.colorbar(im)

            # show plot with labels
            ax.set_xticks(np.arange(len(df_pivot.columns)))
            ax.set_yticks(np.arange(len(df_pivot.columns)))
            ax.set_xticklabels(df_pivot.columns, rotation=30, ha="left")
            # ax.set_xticklabels(df_pivot.columns)
            ax.set_yticklabels(df_pivot.index)
            plt.xlabel("Reference System", fontdict={"weight":"bold"})
            plt.ylabel("Other System", fontdict={"weight":"bold"})
            if tool == "dfba":
                bar.set_label("BF10", fontdict={"weight":"bold"})
            else:
                bar.set_label("P-Value", fontdict={"weight":"bold"}, labelpad=15)

            # Save plot
            plt.savefig(plot_dir / f"{tool}_{cur_exp}.pdf")
            plt.close()


###############################################################################
# Wrapping for directly calling the scripts
###############################################################################
if __name__ == "__main__":
    main()

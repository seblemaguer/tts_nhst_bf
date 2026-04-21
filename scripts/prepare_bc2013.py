#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <sebastien.lemaguer@helsinki.fi>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 20 toukokuu 2026
"""

# Core Python
import argparse

# Messaging/logging
import logging
from logging.config import dictConfig
try:
    import pythonjsonlogger
    JSON_LOGGER = True
except Exception:
    JSON_LOGGER = False

import pandas as pd

###############################################################################
# global constants
###############################################################################
LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]

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
                '()': 'pythonjsonlogger.json.JsonFormatter',
                'fmt': '%(asctime)s %(levelname)s %(filename)s %(lineno)d %(message)s',
                'rename_fields': {'asctime': 'time', 'levelname': 'level', 'lineno': 'line_number'}
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

    # Add arguments
    parser.add_argument("bc2013_df_file", help="The BC2013 DataFrame file")
    parser.add_argument("analysis_df_file", help="The dataframe file produced for analysis")

    # Return parser
    return parser


###############################################################################
# Entry point
###############################################################################
def main():
    # Initialization of the argument parser and the logger
    arg_parser = define_argument_parser()
    args = arg_parser.parse_args()
    logger = configure_logger(args)

    df = pd.read_csv(args.bc2013_df_file, sep="\t")

    # FIXME: order of subjects is the same, but it would be good to have the utterance ID
    df["section_id"] = -1
    df["audio"] = -1 # NOTE: this is a mockup to distinguish two file, THIS IS NOT the real ID
    for _, subdf in df.groupby(["UID"]):
        for i, (i_row, _) in enumerate(subdf.iterrows()):
            df.loc[i_row, "section_id"] = i
            df.loc[i_row, "step_idx"] = i
            df.loc[i_row, "audio"] = i

    # rename system names and melt to be consistent with the analysis scripts
    systems = [x.replace("02_", "") for x in df.columns if x.startswith("02_")]
    df = df.rename(columns={f"02_{x}": x for x in systems})
    df = pd.melt(df, id_vars=set(df.columns) - set(systems), value_vars=systems, var_name="system", value_name="score")

    # Add required columns for the R analysis script
    df["score_type"] = "MOS"
    df["experiment"] = "2013_original"
    df = df.rename(columns={"UID": "user_id"})
    df = df.loc[(df.section_id == 0) | (df.section_id == 2)]

    # Dump the file
    df.to_csv(args.analysis_df_file, index=False, sep="\t")

###############################################################################
# Wrapping for directly calling the scripts
###############################################################################
if __name__ == "__main__":
    main()

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
BASE = 5

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

    # Performative options
    parser.add_argument("-m", "--mushra", action="store_true", help="consider the ranking score as a mushra score")
    parser.add_argument("-e", "--experiment", default=None, type=str, help="the name of the experiment to be appended")

    # Add arguments
    parser.add_argument("source_df_file", help="The BC2013 DataFrame file")
    parser.add_argument("processed_df_file", help="The dataframe file produced for analysis")

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

    # TODO: your code comes here
    df = pd.read_csv(args.source_df_file, sep="\t")

    # Filter out the unwanted scores
    df = df.loc[df.info_type.str.startswith("rank_score")]

    # Add required columns and rename others for the R analysis script
    df["info_type"] = "MUSHRA" if args.mushra else "Ranking"
    df["experiment"] = args.experiment
    df["section_id"] = "test"
    df = df.rename(columns={"info_value": "score", "info_type": "score_type"})
    df["score"] = pd.to_numeric(df["score"])
    print(df.shape)

    # Filter problematic listeners
    if args.mushra:
        valid_listeners = df.loc[(df.system == "Natural") & (df.score > 95), ["user_id", "step_idx"]]
        keys = list(valid_listeners.columns.values)
        i1 = df.set_index(keys).index
        i2 = valid_listeners.set_index(keys).index
        df = df[i1.isin(i2)]
        df.reset_index(drop=True, inplace=True)
    else:
        valid_listeners = df.loc[(df.system == "Degraded") & (df.score == -1), ["user_id", "step_idx"]]
        keys = list(valid_listeners.columns.values)
        i1 = df.set_index(keys).index
        i2 = valid_listeners.set_index(keys).index
        df = df[i1.isin(i2)]
        df.reset_index(drop=True, inplace=True)
        df = df.loc[df.system != "Degraded"]


    # From Ranking to scores
    if not args.mushra:
        systems =list(df.system.unique())
        nb_sys = len(systems)
        df = pd.pivot_table(df, values="score", index=["user_id", "step_idx", "score_type", "experiment", "section_id"], columns=["system"]).reset_index()
        updated_df = []
        for index, cur_row in df.iterrows():
            dict_row = cur_row[systems].to_dict()
            sorted_row = sorted(dict_row.items(), key=lambda x:x[1])
            logger.debug(sorted_row)
            prev = 1
            prev_score = nb_sys
            for i_score, row_elts in enumerate(sorted_row):
                val = row_elts[1]
                if val == prev:
                    prev = val
                    val = prev_score
                else:
                    prev_score = nb_sys - i_score
                    prev = val
                    val = prev_score
                cur_row[row_elts[0]] = val
            updated_df.append(cur_row)
            sorted_row = sorted(dict_row.items(), key=lambda x:x[1], reverse=True)
            logger.debug(sorted_row)

        df = pd.DataFrame(updated_df)
        df = pd.melt(df, id_vars=set(df.columns) - set(systems), value_vars=systems, var_name="system", value_name="score")
    else:
        df["score"] = BASE * round(df["score"]/BASE)

    # Dump the file
    df.to_csv(args.processed_df_file, index=False, sep="\t")

###############################################################################
# Wrapping for directly calling the scripts
###############################################################################
if __name__ == "__main__":
    main()

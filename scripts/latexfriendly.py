import sys
import pandas as pd

DICT_NAME2SHORTS = {
    "tacotron_wg": "T-G",
    "tacotron_wn": "T-N",
    "fastpitch_wg": "F-G",
    "fastpitch_wn": "F-N",
    "Tacotron_WaveGAN": "T-G",
    "Tacotron_WaveNET": "T-N",
    "Tacotron_WaveNet": "T-N",
    "FastPitch_WaveGAN": "F-G",
    "FastPitch_WaveNET": "F-N",
    "FastPitch_WaveNet": "F-N",
    "natural16": "A-16",
    "Natural": "A-16",
}

DICT_COLUMNS = {
    "mean": "Mean",
    "median": "Median",
    "count": "Count",
    "std.dev": "Std",
    "system_1": "System",
    "nbr.val": "Count",
    "CI.mean.0.95": "CI +/- 0.05",
    "average_rank": "Avg. Rank",
}

if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1], sep="\t")
    df.replace(DICT_NAME2SHORTS, inplace=True)
    df.rename(DICT_COLUMNS, axis=1, inplace=True)
    df.sort_values(by="Mean", inplace=True, ascending=False)
    df.to_csv(sys.argv[2], index=False, sep="\t")

import pandas as pd
import sys

# Load CSV file
df = pd.read_csv(sys.argv[1], sep=",", index_col=False)

# Now deal with score
list_lines = []
i_step = -1
i_prev_listener = -1
for _, row in df.iterrows():
    row_dict = row.to_dict()

    # Ensure the step id is consistent
    cur_listener = row_dict["participant"]
    if i_prev_listener != cur_listener:
        i_step = -1
        i_prev_listener = cur_listener

    i_step += 1
    compared_systems = eval(row_dict["systems_compared"])
    for cur_system in compared_systems:
        cur_dict = {}
        cur_dict.update(row_dict)
        cur_dict["step_idx"] = i_step
        score = 2
        if row_dict["best_system"] == cur_system:
            score = 3
        elif row_dict["worst_system"] == cur_system:
            score = 1
        cur_dict["system"] = cur_system
        cur_dict["score"] = score
        cur_dict["score_type"] = "BWS"
        cur_dict["section_id"] = "section_bws"

        list_lines.append(cur_dict)

# Generate dataframe and final preparation
df = pd.DataFrame(list_lines)
df.rename(columns={"participant": "user_id"}, inplace=True)
df["experiment"] = "extended"

# Filter
df.to_csv(sys.argv[2], sep="\t", index=False)

#!/bin/bash

#######################################################################################################
## Switch to configure the script
#######################################################################################################
: ${PREPARE:="TRUE"}
: ${ANALYSIS:="TRUE"}
: ${COLLECT:="TRUE"}
: ${PLOT:="TRUE"}
: ${ROOT_OUTPUT_DIR:="output"}
: ${INPUT_EXPES_FILE:="expes.tsv"}
declare -a TOOLS=("dfba" "bayesics" "wilcoxon" "shapiro" "ttest")
read -r -a SCORES <<< $(tail -n +2 "${INPUT_EXPES_FILE}" | grep -v "^#" | cut -d $'\t' -f 3 | sort -u | tr $'\n' ' ') # NOTE: column 3 is imposed to be the score name

#######################################################################################################
## Helpers
#######################################################################################################
function join_by {
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}

mkdir -p $ROOT_OUTPUT_DIR/log

#######################################################################################################
## Prepare everything
#######################################################################################################

if [[ "${PREPARE}" == "TRUE" ]]; then
    for score in "${SCORES[@]}"; do
        mkdir -p prepared_datasets/${score}
    done

    # Prepare BTTF
    sed 's/Naturalness/MOS/g' ./datasets/MOS/bttf/final.tsv | grep -v "test_section_1" >  prepared_datasets/MOS/bttf.tsv
    python scripts/prepare_ext_bc2013.py -e "only_dnn" -m datasets/MUSHRA/bttf.tsv prepared_datasets/MUSHRA/bttf.tsv
    python scripts/prepare_ext_bc2013.py -e "only_dnn" datasets/Ranking/bttf.tsv prepared_datasets/Ranking/bttf.tsv

    # Prepare BC2025
    head -n 1 ./datasets/MOS/blizzard/2025/BH1/a3_listening-effort_raw.tsv | sed "s/info_type/score_type/g" | sed "s/info_value/score/g" | sed "s/$/\texperiment\tsection_id/g" > prepared_datasets/MOS/BC2025_listening_effort.tsv
    tail -n +2 ./datasets/MOS/blizzard/2025/BH1/a3_listening-effort_raw.tsv | sed "s/mos_listening_effort/MOS/g" | sed "s/$/\t2025_listening_effort\tsection_4/g" >> prepared_datasets/MOS/BC2025_listening_effort.tsv
    head -n 1 ./datasets/MOS/blizzard/2025/BH1/a1_naturalness_raw.tsv | sed "s/info_type/score_type/g" | sed "s/info_value/score/g" | sed "s/$/\texperiment\tsection_id/g" > prepared_datasets/MOS/BC2025_naturalness.tsv
    tail -n +2 ./datasets/MOS/blizzard/2025/BH1/a1_naturalness_raw.tsv | sed "s/mos_naturalness/MOS/g" | sed "s/$/\t2025_naturalness\tsection_4/g" >> prepared_datasets/MOS/BC2025_naturalness.tsv
fi

#######################################################################################################
## Run the analysis
#######################################################################################################
if [[ "${ANALYSIS}" == "TRUE" ]]; then
    python scripts/batch_process.py "${INPUT_EXPES_FILE}" ${ROOT_OUTPUT_DIR}/data 2> /dev/stdout | tee $ROOT_OUTPUT_DIR/log/analysis.log
fi

#######################################################################################################
## Collect and format the output data files
#######################################################################################################
if [[ "${COLLECT}" == "TRUE" ]]; then
    for score in "${SCORES[@]}"; do
        ## Collect the statistical analysis
        #  - Add header
        expe=$(ls "${ROOT_OUTPUT_DIR}/data/${score}" -1 | grep -ve ".\(tsv\|pdf\)" | head -n 1)
        for tool in "${TOOLS[@]}"; do
            head -n 1 "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/${tool}.tsv" > "${ROOT_OUTPUT_DIR}/data/${score}/${tool}.tsv"
        done

        #  - Add content
        expes=$(ls ${ROOT_OUTPUT_DIR}/data/${score} -1 | grep -ve ".\(tsv\|pdf\)")
        for tool in "${TOOLS[@]}"; do
            for expe in $expes; do
                tail -n +2 "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/${tool}.tsv" >> "${ROOT_OUTPUT_DIR}/data/${score}/${tool}.tsv"
            done
        done


        ## Collect the descriptive statistics
        #  - Add header
        expe=$(ls "${ROOT_OUTPUT_DIR}/data/${score}" -1 | grep -ve ".\(tsv\|pdf\)" | head -n 1)
        head -n 1 "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/statistics.tsv" > "${ROOT_OUTPUT_DIR}/data/${score}/statistics.tsv"

        #  - Add content
        expes=$(ls ${ROOT_OUTPUT_DIR}/data/${score} -1 | grep -ve ".\(tsv\|pdf\)")
        for expe in $expes; do
            tail -n +2 "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/statistics.tsv" >> "${ROOT_OUTPUT_DIR}/data/${score}/statistics.tsv"
        done

        #  - Generate per-expe latex friendly TSV files
        for expe in $expes; do
            python scripts/latexfriendly.py "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/statistics.tsv" "${ROOT_OUTPUT_DIR}/data/${score}/${expe}/statistics_show.tsv"
        done
    done
fi

#######################################################################################################
## Plots
#######################################################################################################

if [[ "${PLOT}" == "TRUE" ]]; then
    # NOTE: column 2 in the expes file is imposed to be the experiment name
    for score in "${SCORES[@]}"; do
        python scripts/plot.py -s $(tail -n +2 "${INPUT_EXPES_FILE}" | grep -v "^#" | cut -d $'\t' -f 2 | sort -u | tr '\n' ',' | sed 's/,$//g') $(join_by "," ${TOOLS[@]}) "${ROOT_OUTPUT_DIR}/data/${score}" "${ROOT_OUTPUT_DIR}/figures/${score}"
    done

    # Plot continuous score
    for score in "${SCORES[@]}"; do
        python scripts/plot.py $(tail -n +2 "${INPUT_EXPES_FILE}" | grep -v "^#" | cut -d $'\t' -f 2 | sort -u | tr '\n' ',' | sed 's/,$//g') $(join_by "," ${TOOLS[@]}) "${ROOT_OUTPUT_DIR}/data/${score}" "${ROOT_OUTPUT_DIR}/figures_cont/${score}"
    done
fi

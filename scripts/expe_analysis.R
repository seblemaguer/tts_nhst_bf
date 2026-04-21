#!/usr/bin/env Rscript

## Load the libraries
library(tidyr)
library(dplyr)
library(pastecs)
library(DFBA)
library(csranks)
library(bayesics) ## https://cran.r-project.org/web/packages/bayesics/refman/bayesics.html
library(ggplot2)
library(stats)
library("optparse")


##########################################################################################################################################
### Helper functions
##########################################################################################################################################

scores2ranks <- function(df, systems) {
    df[systems] <- t(apply(df[systems], 1, function(x) {irank(x, increasing=FALSE)}))
    return(df)
}

desc_statistics <- function(input_df, system) {
    BW <- stat.desc(input_df[[system]], norm=TRUE)
    BW <- data.frame(t(unlist(BW)))
    BW["system_1"] = system
    return(BW)
}

dfba_analysis <- function(input_df, system_1, system_2, plot_output_dir=NULL) {

    ## Compute statistics & dump the raw information using dfba
    BW <- dfba_wilcoxon(Y1 = input_df[[system_1]], Y2 = input_df[[system_2]])

    ## Save plot
    if (!is.null(opt$plot_output_dir)) {
        if (! file.exists(plot_output_dir)) {
            dir.create(plot_output_dir, recursive=TRUE)
        }

        plot_output_file = sprintf("%s/%s_%s.pdf", plot_output_dir, system_1, system_2)
        pdf(file=plot_output_file)
        plot(BW)
        dev.off()
        ## ggsave(opt$plot_output_file, width = 20, height = 10, units = "cm")
    }

    ## FIXME: Dirty hack to deal with the parameters
    BW <- data.frame(t(unlist(BW)))
    BW = data.frame(
        system_1 = system_1,
        system_2 = system_2,
        BF10 = BW['BF10']
    )

    return(BW)
}

bayesics_analysis <- function(input_df, system_1, system_2, plot_output_dir=NULL,threshold=0.01) {

    pdf(NULL)
    BW <- wilcoxon_test_b(
        input_df[[system_1]],
        input_df[[system_2]],
        ROPE = threshold,
        plot = !is.null(plot_output_dir)
        ## paired = FALSE,
        ## p = 0.5,
        ## ROPE = 0.05,
        ## prior = "centered",
        ## prior_shapes,
        ## CI_level = 0.95,
        ## seed = 1
    )
    dev.off()

    ## Save plot
    if (!is.null(plot_output_dir)) {
        if (! file.exists(plot_output_dir)) {
            dir.create(plot_output_dir, recursive=TRUE)
        }
        plot_output_file = sprintf("%s/%s_%s.pdf", plot_output_dir, system_1, system_2)
        ggsave(plot_output_file, width = 20, height = 10, units = "cm")
    }

    ## Remove the plot now that it is plotted and save the analysis
    # BW = data.frame(t(unlist(BW))) # FIXME: why is this failing.
    BW["prob_plot"] = ""
    BW["dfba_wilcoxon_object"] = ""
    BW["system_1"] = system_1
    BW["system_2"] = system_2

    return(BW)
}

wilcoxon_analysis <- function(input_df, system_1, system_2) {

    BW = wilcox.test(
        input_df[[system_1]],
        input_df[[system_2]],
        paired=TRUE
    )
    BW = data.frame(t(unlist(BW)))
    BW["data.name"] = ""
    BW["null.value"] = ""
    BW["system_1"] = system_1
    BW["system_2"] = system_2

    return(BW)
}


shapiro_analysis <- function(input_df, system_1) {

    BW = shapiro.test(
        input_df[[system_1]]
    )
    BW = data.frame(t(unlist(BW)))
    BW["data.name"] = ""
    BW["null.value"] = ""
    BW["system_1"] = system_1

    return(BW)
}

ttest_analysis <- function(input_df, system_1, system_2) {

    BW = t.test(
        input_df[[system_1]],
        input_df[[system_2]],
        paired=TRUE
    )
    BW = data.frame(t(unlist(BW)))
    BW["data.name"] = ""
    BW["null.value"] = ""
    BW["system_1"] = system_1
    BW["system_2"] = system_2

    return(BW)
}

plackettluce_analysis <- function(input_df, system_1, system_2) {

    BW = t.test(
        input_df[[system_1]],
        input_df[[system_2]],
        paired=TRUE
    )
    BW = data.frame(t(unlist(BW)))
    BW["data.name"] = ""
    BW["null.value"] = ""
    BW["system_1"] = system_1
    BW["system_2"] = system_2

    return(BW)
}


##########################################################################################################################################
### Program part
##########################################################################################################################################

## Command line
option_list = list(
    make_option(c("-A", "--audio"), action = "store_true", default = FALSE,
                help="audio level grouping"),
    make_option(c("-B", "--with_bonferroni_correction"), action = "store_true", default=FALSE,
                help="Correct the p-value with the Bonferroni correction"),
    make_option(c("-S", "--step_idx"), action = "store_true", default=FALSE,
                help="Take the step idx into account into the grouping index"),
    make_option(c("-e", "--experiment"), type="character", default=NULL,
                help="experiment label", metavar="character"),
    make_option(c("-i", "--input_file"), type="character", default=NULL,
                help="dataset file name", metavar="character"),
    make_option(c("-d", "--output_dfba_file"), type="character", default=NULL,
                help="the raw results file name", metavar="character"),
    make_option(c("-b", "--output_bayesics_file"), type="character", default=NULL,
                help="the raw results file name", metavar="character"),
    make_option(c("-n", "--output_shapiro_file"), type="character", default=NULL,
                help="the raw results file name", metavar="character"),
    make_option(c("-t", "--output_ttest_file"), type="character", default=NULL,
                help="the raw results file name", metavar="character"),
    make_option(c("-w", "--output_wilcoxon_file"), type="character", default=NULL,
                help="the raw results file name", metavar="character"),
    make_option(c("-o", "--output_file"), type="character", default="statistics.txt",
                help="the raw results file name [default= %default]", metavar="character"),
    make_option(c("-s", "--score_name"), type="character", default=NULL,
                help="the name of the score (case sensitive!)", metavar="character"),
    make_option(c("--plot_output_dir"), type="character", default=NULL,
                help="the output directory to contain all the plots generated with DFBA", metavar="character"),
    make_option(c("--plot_output_bayesics_dir"), type="character", default=NULL,
                help="the output directory to contain all the plots generated with bayesics", metavar="character")
);

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

## Load blizzard dataframe
input_df <- read.csv(opt$input_file, sep="\t")

## List experiments
cur_experiment <- opt$experiment
experiments <- unique(input_df[["experiment"]])
print(experiments)
cur_score <- opt$score_name

## Prepare required output directories
print("######################################################################")
print(sprintf("## %s", cur_experiment))
print("######################################################################")

plot_output_dir <- sprintf("%s/%s", opt$plot_output_dir, cur_experiment)
if (!is.null(opt$plot_output_bayesics_dir)) {
    plot_output_bayesics_dir <- sprintf("%s/%s", opt$plot_output_bayesics_dir, cur_experiment)
} else {
    plot_output_bayesics_dir <- NULL
}

## Define the columns to load
id_columns <- c("user_id", "section_id")
if (opt$audio) { id_columns <- c(id_columns, "audio") }
if (opt$step_idx) { id_columns <- c(id_columns, "step_idx") }
columns <- c(id_columns, "system", "score")

## Extract subframe of the experiment and the systems
experiment_df <- subset(x=input_df, subset=(experiment==cur_experiment & score_type==cur_score), select=columns)

## there are some duplicates, we deal with this by using the mean of the duplicate
experiment_df <- experiment_df %>% group_by_at(c(id_columns, "system")) %>% summarise(score=mean(score))

## Finally generate the dataframe to be analysed
systems <- unique(experiment_df[["system"]])
experiment_df <- experiment_df %>% pivot_wider(names_from="system", values_from="score")
ranks_df <- scores2ranks(experiment_df[complete.cases(experiment_df), ], systems)
print("\n=====================  Head of the data  =====================\n")
print(head(experiment_df))
print("\n========================== Analysis ==========================\n")

## Run all the analysis
dfba_bws = NULL
bayesics_bws = NULL
wilcoxon_bws = NULL
shapiro_bws = NULL
ttest_bws = NULL
desc_bws = NULL


for (i_system_1 in 1:length(systems)) {
    system_1 = systems[i_system_1]
    if (!is.null(opt$output_shapiro_file)) {
        bw_shapiro <- shapiro_analysis(experiment_df, system_1)
        bw_shapiro["experiment"] = cur_experiment
        shapiro_bws <- rbind(shapiro_bws, bw_shapiro)
    }

    bw_desc <- desc_statistics(experiment_df, system_1)
    bw_desc["average_rank"] <- mean(ranks_df[[system_1]])
    desc_bws <- rbind(desc_bws, bw_desc)

    for (i_system_2 in 1:length(systems)) {
        system_2 = systems[i_system_2]
        if (system_1 == system_2) {
            next
        }

        print(sprintf("## %s / %s", system_1, system_2))
        bw_dfba <- dfba_analysis(experiment_df, system_1, system_2, plot_output_dir)
        bw_dfba["experiment"] = cur_experiment
        dfba_bws <- rbind(dfba_bws, bw_dfba)

        if (!is.null(opt$output_bayesics_file)) {
            bw_bayesics <- bayesics_analysis(experiment_df, system_1, system_2, plot_output_bayesics_dir)
            bw_bayesics["experiment"] = cur_experiment
            bayesics_bws <- rbind(bayesics_bws, bw_bayesics)
        }

        if (!is.null(opt$output_wilcoxon_file)) {
            bw_wilcoxon <- wilcoxon_analysis(experiment_df, system_1, system_2)
            bw_wilcoxon["experiment"] = cur_experiment
            wilcoxon_bws <- rbind(wilcoxon_bws, bw_wilcoxon)
        }
        if (!is.null(opt$output_ttest_file)) {
            bw_ttest <- ttest_analysis(experiment_df, system_1, system_2)
            bw_ttest["experiment"] = cur_experiment
            ttest_bws <- rbind(ttest_bws, bw_ttest)
        }
    }
}

if(opt$with_bonferroni_correction) {
    shapiro_bws$p.value = p.adjust(shapiro_bws$p.value, method="bonferroni")

    ## NOTE: hardcore coded to as we compute a symmetric version (for now)
    wilcoxon_bws$p.value <- as.numeric(wilcoxon_bws$p.value)
    wilcoxon_bws$p.value <- pmin(1, (length(wilcoxon_bws$p.value)/2) * wilcoxon_bws$p.value)
    ttest_bws$p.value <- as.numeric(ttest_bws$p.value)
    ttest_bws$p.value <- pmin(1, (length(ttest_bws$p.value)/2) * ttest_bws$p.value)
}

## Save dataframes
desc_bws <- desc_bws[order(-desc_bws$average_rank, decreasing = TRUE),,drop=FALSE]
write.table(desc_bws, file = opt$output_file, sep="\t", row.names=FALSE, quote=FALSE)
write.table(dfba_bws, file = opt$output_dfba_file, sep="\t", row.names=FALSE, quote=FALSE)
if (!is.null(opt$output_bayesics_file)) {
    write.table(bayesics_bws, file = opt$output_bayesics_file, sep="\t", row.names=FALSE, quote=FALSE)
}
if (!is.null(opt$output_wilcoxon_file)) {
    write.table(wilcoxon_bws, file = opt$output_wilcoxon_file, sep="\t", row.names=FALSE, quote=FALSE)
}
if (!is.null(opt$output_ttest_file)) {
    write.table(ttest_bws, file = opt$output_ttest_file, sep="\t", row.names=FALSE, quote=FALSE)
}
if (!is.null(opt$output_shapiro_file)) {
    write.table(shapiro_bws, file = opt$output_shapiro_file, sep="\t", row.names=FALSE, quote=FALSE)
}

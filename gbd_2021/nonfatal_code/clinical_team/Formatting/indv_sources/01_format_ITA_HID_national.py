import pandas as pd
import platform
import numpy as np
import sys
import warnings
import os
import re
import getpass
import time

user = getpass.getuser()
prep_path = r"FILEPATH"
sys.path.append(prep_path)

from hosp_prep import *

# Environment:
if platform.system() == "Linux":
    root = "FILEPATH"
else:
    root = "FILEPATH"

#####################################################
# READ DATA AND KEEP RELEVANT COLUMNS
# ASSIGN FEATURE NAMES TO OUR STRUCTURE
#####################################################


def read_raw_data(write_data=False):
    """
    ITA data is stored by year in stata files that take awhile to read in.
    These were read in once, the desired columns were kept and data was
    written to the location above in /raw
    """
    years = np.arange(2005, 2017, 1)
    # years = [2006]
    df_list = []
    sdict = {}
    for year in years:
        print("Starting on year {}".format(year))
        start = time.time()
        if year == 2007:
            print("2007 Stata is corrupted as of 2018-01-12")
            fpath = "FILEPATH"
            df = pd.read_sas(fpath)
        else:
            # read from stata
            fpath = r"FILEPATH"
            df = pd.read_stata(fpath)
            read_time = (time.time() - start) / 60
            print("It took {} min to read in year {}".format(read_time, year))
            # df = pd.read_sas(filepath)
            sdict[year] = df.columns.tolist()

        try:
            # give keeping these cols a shot
            ideal_keep = [
                "sesso",
                "eta",
                "reg_ric",
                "regric",
                "gg_deg",
                "mod_dim",
                "mot_dh",
                "tiporic",
                "dpr",
                "dsec1",
                "dsec2",
                "dsec3",
                "dsec4",
                "dsec5",
                "causa_ext",
                "tip_ist2",
                "data_ric",
                "data_dim",
                "data_ricA",
                "data_dimA",
            ]
            to_keep = [n for n in ideal_keep if n in df.columns]
            print(
                (
                    "Missing {} for this year".format(
                        [n for n in ideal_keep if n not in df.columns]
                    )
                )
            )
            df = df[to_keep]
            df["year_start"] = year
            df_list.append(df)
        except:
            print("well that didn't work for {}".format(year))
        del df

    if write_data:
        df = pd.concat(df_list, ignore_index=True)

        df.loc[(df.data_ric.isnull()) & (df.data_ricA.notnull()), "data_ric"] = df.loc[
            (df.data_ric.isnull()) & (df.data_ricA.notnull()), "data_ricA"
        ]
        df.loc[(df.data_dim.isnull()) & (df.data_dimA.notnull()), "data_dim"] = df.loc[
            (df.data_dim.isnull()) & (df.data_dimA.notnull()), "data_dimA"
        ]

        df.drop(["data_ricA", "data_dimA"], axis=1, inplace=True)

        df["gg_deg"] = pd.to_numeric(df.gg_deg, errors="raise")

        write_hosp_file(
            df, "FILEPATH",
        )
    return df_list


final_list = []
# for year in back.year_start.sort_values().unique():
years = np.arange(2005, 2017, 1)
for year in years:
    print("Starting on year {}".format(year))
    start = time.time()
    # start = time.time()
    if year == 2007:
        print("2007 Stata is corrupted as of 2018-01-12")
        fpath = "FILEPATH"
        df = pd.read_sas(fpath)
    else:
        # read from stata
        fpath = r"FILEPATH"
        df = pd.read_stata(fpath)
        # read in header
        # df = read_stata_chunks(fpath, chunksize=50000,
        #                             chunks=10)
        read_time = (time.time() - start) / 60
        print("It took {} min to read in year {}".format(read_time, year))
        # df = pd.read_sas(filepath)
        # sdict[year] = df.columns.tolist()

    try:
        # give keeping these cols a shot
        ideal_keep = [
            "sesso",
            "eta",
            "reg_ric",
            "regric",
            "gg_deg",
            "mod_dim",
            "mot_dh",
            "tiporic",
            "dpr",
            "dsec1",
            "dsec2",
            "dsec3",
            "dsec4",
            "dsec5",
            "causa_ext",
            "tip_ist2",
            "data_ric",
            "data_dim",
            "data_ricA",
            "data_dimA",
        ]
        to_keep = [n for n in ideal_keep if n in df.columns]
        print(
            (
                "Missing {} for this year".format(
                    [n for n in ideal_keep if n not in df.columns]
                )
            )
        )
        df = df[to_keep]
        df["year_start"] = year

    except:
        print("well that didn't work for {}".format(year))

    yr_start = time.time()
    print("Starting on year {}".format(year))

    if "data_ricA" in df.columns:
        df.rename(columns={"data_ricA": "data_ric"}, inplace=True)
    if "data_dimA" in df.columns:
        df.rename(columns={"data_dimA": "data_dim"}, inplace=True)
    # df.drop(['data_ricA', 'data_dimA'], axis=1, inplace=True)

    df["gg_deg"] = pd.to_numeric(df.gg_deg, errors="raise")

    # check that dates are always present
    assert not df.data_dim.isnull().sum()
    assert not df.data_ric.isnull().sum()

    # df = back[back.year_start == year].copy()
    start_cases = df.shape[0]

    # Everything in the for loop below is basically our standard formatting steps

    # If this assert fails uncomment this line:
    # df = df.reset_index(drop=True)
    assert df.shape[0] == len(df.index.unique()), (
        "index is not unique, "
        + "the index has a length of "
        + str(len(df.index.unique()))
        + " while the DataFrame has "
        + str(df.shape[0])
        + " rows"
        + "try this: df = df.reset_index(drop=True)"
    )

    # Replace feature names on the left with those found in data where appropriate
    # ALL OF THESE COLUMNS WILL BE MADE unless you comment out the ones you don't
    # want
    hosp_wide_feat = {
        "nid": "nid",
        "location_id": "location_id",
        "representative_id": "representative_id",
        "year_start": "year_start",
        "year_end": "year_end",
        "sesso": "sex_id",
        "eta": "age",
        "age_group_unit": "age_group_unit",
        "code_system_id": "code_system_id",
        "data_dim": "dis_date",
        "data_ric": "adm_date",
        "gg_deg": "los",
        # measure_id variables
        "mod_dim": "outcome_id",
        "tip_ist2": "facility_id",
        # diagnosis varibles
        "dpr": "dx_1",
        "dsec1": "dx_2",
        "dsec2": "dx_3",
        "dsec3": "dx_4",
        "dsec4": "dx_5",
        "dsec5": "dx_6",
        "causa_ext": "ecode_1",
        # look into these later
        "tiporic": "hosp_type",
        "reg_ric": "hosp_scheme",
        "mot_dh": "hosp_reason",
    }

    # Rename features using dictionary created above
    df.rename(columns=hosp_wide_feat, inplace=True)

    # set difference of the columns you have and the columns you want,
    # yielding the columns you don't have yet
    new_col_df = pd.DataFrame(
        columns=list(set(hosp_wide_feat.values()) - set(df.columns))
    )
    df = df.join(new_col_df)

    # drop them for now
    df.drop(["hosp_type", "hosp_scheme", "hosp_reason"], axis=1, inplace=True)

    assert start_cases == df.shape[0], "Some rows were lost or added"

    # drop missing primary dx
    null_count = df.dx_1.isnull().sum()
    # print("null dx 1 is {}".format(null_count))
    warnings.warn(
        "Dropping rows with missing primary dx. {} rows will be dropped".format(
            null_count
        )
    )

    df = df[df.dx_1.notnull()]
    print("next up is empty string dx")

    blank_count = (df.dx_1 == "").sum()
    warnings.warn(
        "Dropping rows with blank primary dx. {} rows will be dropped".format(
            blank_count
        )
    )
    df = df[df.dx_1 != ""]
    start_cases = df.shape[0]

    # swap e and n codes
    # fill missing ecodes with null
    df.loc[df["ecode_1"] == "", "ecode_1"] = np.nan

    if not df[df.year_start == year].ecode_1.isnull().all():
        df["dx_7"] = np.nan
        # put n codes into dx_7 col
        df.loc[df["ecode_1"].notnull(), "dx_7"] = df.loc[
            df["ecode_1"].notnull(), "dx_1"
        ]
        # overwrite n codes in dx_1
        df.loc[df["ecode_1"].notnull(), "dx_1"] = df.loc[
            df["ecode_1"].notnull(), "ecode_1"
        ]
    # drop the ecode col
    df.drop("ecode_1", axis=1, inplace=True)

    #####################################################
    # FILL COLUMNS THAT SHOULD BE HARD CODED
    # this is where you fill in the blanks with the easy
    # stuff, like what version of ICD is in the data.
    #####################################################

    # These are completely dependent on data source

    # -1: "Not Set",
    # 0: "Unknown",
    # 1: "Nationally representative only",
    # 2: "Representative for subnational location only",
    # 3: "Not representative",
    # 4: "Nationally and subnationally representative",
    # 5: "Nationally and urban/rural representative",
    # 6: "Nationally, subnationally and urban/rural representative",
    # 7: "Representative for subnational location and below",
    # 8: "Representative for subnational location and urban/rural",
    # 9: "Representative for subnational location, urban/rural and below",
    # 10: "Representative of urban areas only",
    # 11: "Representative of rural areas only"

    df["representative_id"] = 1  # Do not take this as gospel, it's guesswork
    df["location_id"] = 86

    # group_unit 1 signifies age data is in years
    df["age_group_unit"] = 1
    df["source"] = "ITA_HID"

    # code 1 for ICD-9, code 2 for ICD-10
    df["code_system_id"] = 1

    # case is the sum of live discharges and deaths
    # df['outcome_id'] = "case/discharge/death"
    # df['outcome_id'] = df['outcome_id'].str.decode('ascii')
    df["outcome_id"].replace(["1"], ["death"], inplace=True)
    df.loc[df["outcome_id"] != "death", "outcome_id"] = "discharge"

    # metric_id == 1 signifies that the 'val' column consists of counts
    df["metric_id"] = 1

    df["year_end"] = df["year_start"]

    # remove x value from sex_id
    df.loc[df.sex_id == "X", "sex_id"] = 3

    # keep these but commented out if we ever look more into these vars
    # df.loc[df.hosp_scheme == 'X', 'hosp_scheme'] = 0
    # df.loc[df.hosp_type == "", 'hosp_type'] = np.nan

    # this is hospital discharge data
    df["facility_id"] = "hospital"

    # fix data types
    # num_cols = ['hosp_scheme', 'sex_id', 'hosp_type']
    num_cols = ["sex_id"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="raise")

    diag_cols = df.filter(regex="^dx_|^ecode_").columns

    # below was necessary to process sas files
    # diagnosis columns should be ascii instead of byte
    # for col in diag_cols:
    #    df[col] = df[col].str.decode('ascii')

    # date cols to datetime obj
    for date_type in ["adm_date", "dis_date"]:
        df[date_type] = pd.to_datetime(df[date_type], errors="coerce")
        nulls = df[date_type].isnull().sum()
        if nulls > 0:
            warnings.warn("Dropping {} null date rows".format(nulls))
            df = df[df[date_type].notnull()]

    start_cases = df.shape[0]

    df["los2"] = df["dis_date"].subtract(df["adm_date"])
    df["los2"] = df["los2"].dt.days

    df[df.los != df.los2].shape

    assert start_cases == df.shape[0]
    # remove day cases
    # print("describe los2 col {}".format(df.los2.describe()))
    print(("There are {} rows with los2 less than 0".format((df.los2 < 0).sum())))

    # remove day cases and negative stay (nonsense) cases
    df = df[df.los2 > 0]
    end_cases = start_cases - df.shape[0]
    print(
        (
            "{} cases were lost when dropping day cases. or {} ".format(
                end_cases, float(end_cases) / df.shape[0]
            )
        )
    )
    int_cases = df.shape[0]

    df.drop(["los", "los2"], axis=1, inplace=True)

    # Create a dictionary with year-nid as key-value pairs
    nid_dictionary = {
        2005: 331137,
        2006: 331138,
        2007: 331139,
        2008: 331140,
        2009: 331141,
        2010: 331142,
        2011: 331143,
        2012: 331144,
        2013: 331145,
        2014: 331146,
        2015: 331147,
        2016: 331148,
    }
    df = fill_nid(df, nid_dictionary)

    #####################################################
    # CLEAN VARIABLES
    #####################################################

    # Columns contain only 1 optimized data type
    int_cols = [
        "location_id",
        "year_start",
        "year_end",
        "age_group_unit",
        "age",
        "sex_id",
        "nid",
        "representative_id",
        "metric_id",
    ]

    # BE CAREFUL WITH NULL VALUES IN THE STRING COLUMNS, they will be converted
    # to the string "nan"
    # fast way to cast to str while preserving Nan:
    # df['casted_foo'] = df.foo.loc[df.foo.notnull()].map(str)
    str_cols = ["source", "facility_id", "outcome_id"]

    # use this to infer data types
    # df.apply(lambda x: pd.lib.infer_dtype(x.values))

    if df[str_cols].isnull().any().any():
        warnings.warn(
            "\n\n There are NaNs in the column(s) {}".format(
                df[str_cols].columns[df[str_cols].isnull().any()]
            )
            + "\n These NaNs will be converted to the string 'nan' \n"
        )

    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="raise", downcast="integer")
    for col in str_cols:
        df[col] = df[col].astype(str)

    # Turn 'age' into 'age_start' and 'age_end'
    #   - bin into year age ranges
    #   - under 1, 1-4, 5-9, 10-14 ...

    df.loc[df["age"] > 95, "age"] = 95  # this way everything older than GBD
    # terminal age start will be lumped into the terminal age group.
    df = age_binning(df)

    # drop unknown sex_id
    df.loc[(df["sex_id"] != 1) & (df["sex_id"] != 2), "sex_id"] = 3

    # drop unneeded columns, review hospital types
    for col in ["age", "regric", "dis_date", "adm_date"]:
        if col in df.columns:
            df.drop(col, axis=1, inplace=True)
    # df.drop(['age', 'regric',
    #          'dis_date', 'adm_date'], axis=1, inplace=True)

    # store the data wide for the EN matrix
    df_wide = df.copy()
    df_wide["metric_discharges"] = 1
    # any rows with a null get dropped in the groupby, fill these missing values with ""
    dxs = df_wide.filter(regex="^dx_").columns.tolist()
    for dxcol in dxs:
        df_wide[dxcol].fillna("", inplace=True)
        df_wide[dxcol] = sanitize_diagnoses(df_wide[dxcol])
    print("Missing values", df_wide.isnull().sum())
    assert (df_wide.isnull().sum() == 0).all()
    df_wide = (
        df_wide.groupby(df_wide.columns.drop("metric_discharges").tolist())
        .agg({"metric_discharges": "sum"})
        .reset_index()
    )
    df_wide.to_stata(r"FILEPATH")
    write_path = r"FILEPATH"
    write_hosp_file(df_wide, write_path, backup=False)
    del df_wide

    #####################################################
    # IF MULTIPLE DX EXIST:
    # TRANSFORM FROM WIDE TO LONG
    #####################################################
    pre_reshape_rows = df.shape[0]

    # Find all columns with dx_ at the start
    diagnosis_feats = df.columns[df.columns.str.startswith("dx_")]
    # Remove non-alphanumeric characters from dx feats
    for feat in diagnosis_feats:
        df[feat] = sanitize_diagnoses(df[feat])

    cols = df.columns
    print(df.shape, "shape before reshape")
    if len(diagnosis_feats) > 1:
        # Reshape diagnoses from wide to long
        stack_idx = [n for n in df.columns if "dx_" not in n]
        # print(stack_idx)
        len_idx = len(stack_idx)

        df = df.set_index(stack_idx).stack().reset_index()

        # print(df["level_{}".format(len_idx)].value_counts())

        # drop the empty strings
        pre_dx1 = df[df["level_{}".format(len_idx)] == "dx_1"].shape[0]
        df = df[df[0] != ""]
        diff = pre_dx1 - df[df["level_{}".format(len_idx)] == "dx_1"].shape[0]
        print("{} dx1 cases/rows were lost after dropping blanks".format(diff))

        df = df.rename(
            columns={"level_{}".format(len_idx): "diagnosis_id", 0: "cause_code"}
        )

        df.loc[df["diagnosis_id"] != "dx_1", "diagnosis_id"] = 2
        df.loc[df.diagnosis_id == "dx_1", "diagnosis_id"] = 1

    elif len(diagnosis_feats) == 1:
        df.rename(columns={"dx_1": "cause_code"}, inplace=True)
        df["diagnosis_id"] = 1

    else:
        print("Something went wrong, there are no ICD code features")

    # If individual record: add one case for every diagnosis
    df["val"] = 1

    print(df.shape, "shape after reshape")

    assert abs(int_cases - df[df.diagnosis_id == 1].val.sum()) < 350
    chk = (
        df.query("diagnosis_id == 1")
        .groupby("source")
        .agg({"diagnosis_id": "sum"})
        .reset_index()
    )
    assert (chk["diagnosis_id"] >= pre_reshape_rows * 0.999).all()
    #####################################################
    # GROUPBY AND AGGREGATE
    #####################################################

    # Check for missing values
    print("Are there missing values in any row?\n")
    null_condition = df.isnull().values.any()
    if null_condition:
        warnings.warn(">> Yes.  ROWS WITH ANY NULL VALUES WILL BE LOST ENTIRELY")
    else:
        print(">> No.")

    # Group by all features we want to keep and sums 'val'
    group_vars = [
        "cause_code",
        "diagnosis_id",
        "sex_id",
        "age_start",
        "age_end",
        "year_start",
        "year_end",
        "location_id",
        "nid",
        "age_group_unit",
        "source",
        "facility_id",
        "code_system_id",
        "outcome_id",
        "representative_id",
        "metric_id",
    ]
    df_agg = df.groupby(group_vars).agg({"val": "sum"}).reset_index()

    #####################################################
    # ARRANGE COLUMNS AND PERFORM INTEGRITY CHECKS
    #####################################################

    # Arrange columns in our standardized feature order
    columns_before = df_agg.columns
    hosp_frmat_feat = [
        "age_group_unit",
        "age_start",
        "age_end",
        "year_start",
        "year_end",
        "location_id",
        "representative_id",
        "sex_id",
        "diagnosis_id",
        "metric_id",
        "outcome_id",
        "val",
        "source",
        "nid",
        "facility_id",
        "code_system_id",
        "cause_code",
    ]
    df_agg = df_agg[hosp_frmat_feat]
    columns_after = df_agg.columns

    # check if all columns are there
    assert set(columns_before) == set(
        columns_after
    ), "You lost or added a column when reordering"
    for i in range(len(hosp_frmat_feat)):
        assert (
            hosp_frmat_feat[i] in df_agg.columns
        ), "%s is missing from the columns of the DataFrame" % (hosp_frmat_feat[i])

    # check data types
    for i in df_agg.drop(
        ["cause_code", "source", "facility_id", "outcome_id"], axis=1, inplace=False
    ).columns:
        # assert that everything but cause_code, source, measure_id (for now)
        # are NOT object
        assert df_agg[i].dtype != object, "%s should not be of type object" % (i)

    # check number of unique feature levels
    assert len(df_agg["year_start"].unique()) == len(
        df_agg["nid"].unique()
    ), "number of feature levels of years and nid should match number"
    assert len(df_agg["age_start"].unique()) == len(df_agg["age_end"].unique()), (
        "number of feature levels age start should match number of feature"
        " levels age end"
    )
    assert (
        len(df_agg["diagnosis_id"].unique()) <= 2
    ), "diagnosis_id should have 2 or less feature levels"

    s = [1, 2, 3]
    check_sex = [n for n in df.sex_id.unique() if n not in s]
    assert len(check_sex) == 0, "There is an unexpected sex_id value"

    assert (
        len(df_agg["code_system_id"].unique()) <= 2
    ), "code_system_id should have 2 or less feature levels"
    assert (
        len(df_agg["source"].unique()) == 1
    ), "source should only have one feature level"

    assert (df.val >= 0).all(), "for some reason there are negative case counts"

    assert abs(int_cases - df[df.diagnosis_id == 1].val.sum()) < 350
    chk = (
        df.query("diagnosis_id == 1")
        .groupby("source")
        .agg({"diagnosis_id": "sum"})
        .reset_index()
    )
    assert (chk["diagnosis_id"] >= pre_reshape_rows * 0.999).all()

    final_list.append(df_agg)
    del df
    del df_agg
    yr_run = (time.time() - yr_start) / 60
    print("Done with {} in {} min".format(year, yr_run))
#####################################################
# WRITE TO FILE
#####################################################

df_agg = pd.concat(final_list, ignore_index=True)
# somehow "nan" is making it through, nulls were cast to string
df_agg = df_agg[df_agg.cause_code != "nan"]
df_agg.info(memory_usage="deep")
print(df_agg.shape)
# # Saving the file
write_path = root + r"FILEPATH"

write_hosp_file(df_agg, write_path, backup=True)

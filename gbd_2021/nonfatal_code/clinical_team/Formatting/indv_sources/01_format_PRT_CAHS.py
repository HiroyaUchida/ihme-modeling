import pandas as pd
import platform
import numpy as np
import sys
from getpass import getuser

# load our functions
from clinical_info.Functions import hosp_prep
from clinical_info.Functions.live_births import live_births

# Environment:
if platform.system() == "Linux":
    root = "FILEPATH"
else:
    root = "FILEPATH"

#####################################################
# READ DATA AND KEEP RELEVANT COLUMNS
# ASSIGN FEATURE NAMES TO OUR STRUCTURE
#####################################################

# read in episodes information
df_episodes = pd.read_excel(root + r"FILEPATH")
df_episodes = df_episodes[["ano", "seq_number", "sexo", "idade", "dsp"]]

# read in diagnosis information
df_diagnoses = pd.read_excel(root + r"FILEPATH")
df_diagnoses = df_diagnoses[
    ["seq_episodio_int", "cod_diagnostico", "tipo_p_s", "ordem"]
]


# try reshaping wide
df_diagnoses = df_diagnoses.pivot(
    index="seq_episodio_int", columns="ordem", values="cod_diagnostico"
).reset_index()

# rename the columns to dx_1, dx_2.... and so on
raw_names = df_diagnoses.filter(regex="^[\d]").columns
col_names = ["seq_episodio_int"]
for col in raw_names:
    col_names.append("dx_" + str(col + 1))
df_diagnoses.columns = col_names

# swap live births
df_diagnoses["code_system_id"] = 1
preswap = df_diagnoses.copy()
df_diagnoses = live_births.swap_live_births(
    df_diagnoses, user=getuser(), drop_if_primary_still_live=False
)
# needed code system, but not sure how it will perform with the reshape and merges
# so just drop it then re-add later
df_diagnoses.drop("code_system_id", axis=1, inplace=True)

# read in external causes information
df_external_causes = pd.read_excel(root + r"FILEPATH")
df_external_causes = df_external_causes[
    [
        "seq_episodio_int",
        "cod_diagnostico",
        "cod_causa_ext",
        "tipo_p_s",
        "ordem",
        "ordem_assoc",
    ]
]

df_external_causes["col_name"] = "broke"
for seq in df_external_causes.seq_episodio_int.unique():
    seq_len = df_external_causes[df_external_causes.seq_episodio_int == seq].shape[0]
    ints = np.arange(1, seq_len + 1, 1)
    to_name = []
    for int in ints:
        to_name.append("ecode_" + str(int))
    df_external_causes.loc[
        df_external_causes.seq_episodio_int == seq, "col_name"
    ] = to_name
assert "broke" not in df_external_causes.col_name.unique(), "The code above broke"
df_external_causes = df_external_causes.pivot(
    index="seq_episodio_int", columns="col_name", values="cod_causa_ext"
).reset_index()

# rename columns to ecode_1, ecode_2, etc
raw_names = df_external_causes.filter(regex="^[\d]").columns
col_names = ["seq_episodio_int"]


# inspect the patient id numbers.  There is some concern, because the variable
# names change between the episodes file and the other two.
len(df_episodes.seq_number.unique())
len(df_diagnoses.seq_episodio_int.unique())
len(df_external_causes.seq_episodio_int.unique())

# since episodes and diagnoses have the same number of unique ids, check if
# the ids are the same by asserting the disjoint set is the empty set
assert (
    set.difference(
        set(df_episodes.seq_number.unique()),
        set(df_diagnoses.seq_episodio_int.unique()),
    )
    == set()
), "ids don't match between sets"

# since external causes have fewer ids than the episodes file, check that all
# the ids in the external causes files are contained within the episodes file.
# demonstartion: set([1]) - set([1,2,3,4]) = set().  We want the empty set:
assert (
    set(df_external_causes.seq_episodio_int.unique())
    - set(df_episodes.seq_number.unique())
    == set()
), "result should be empty set"


# MERGING ALL INFO INTO ONE DATAFRAME
pre_eps = df_diagnoses.seq_episodio_int.unique().size
merged_ex_dx = df_diagnoses.merge(
    df_external_causes,
    how="left",
    on="seq_episodio_int",
    # 'cod_diagnostico', 'tipo_p_s'],
    suffixes=["_diag", "_inj"],
)
assert pre_eps == merged_ex_dx.seq_episodio_int.unique().size, "cases lost"
merged_ex_dx.rename(columns={"seq_episodio_int": "seq_number"}, inplace=True)
assert (
    merged_ex_dx.seq_number.value_counts(dropna=False)
    == df_diagnoses.seq_episodio_int.value_counts(dropna=False)
).all(), "Cases were lost"
df = df_episodes.merge(merged_ex_dx, how="left", on="seq_number")
assert (
    merged_ex_dx.seq_number.value_counts(dropna=False)
    == df.seq_number.value_counts(dropna=False)
).all(), "Cases were lost"
# lose the constituent parts now that we have the whole
# del merged_ex_dx, df_episodes, df_diagnoses, df_external_causes

assert df.shape[0] == len(df.index.unique()), (
    "index is not unique, "
    + "the index has a length of "
    + str(len(df.index.unique()))
    + " while the DataFrame has "
    + str(df.shape[0])
    + " rows"
)

# Select features from raw data to keep
df.drop("seq_number", axis=1, inplace=True)  # don't need it anymore

# Replace feature names on the left with those found in data where appropriate
# ALL OF THESE COLUMNS WILL BE MADE unless you comment out the ones you don't
# want
hosp_wide_feat = {
    "nid": "nid",
    "location_id": "location_id",
    "representative_id": "representative_id",
    "ano": "year",
    #    'year_start': 'year_start',
    #    'year_end': 'year_end',
    "sexo": "sex_id",
    "idade": "age",
    #    'age_start': 'age_start',
    #    'age_end': 'age_end',
    "age_group_unit": "age_group_unit",
    "code_system_id": "code_system_id",
    # measure_id variables
    "dsp": "outcome_id",
    "adm_tip": "facility_id",
    # diagnosis varibles
    # THIS DATA HAS MULT DX LONG ALREADY
    #    'dx_1': 'dx_1',
    #    'dx_2': 'dx_2',
    #    'dx_3': 'dx_3'
    # source specific vars
    # "tipo_p_s": "diagnosis_id"
}

# Rename features using dictionary created above
df.rename(columns=hosp_wide_feat, inplace=True)

# set difference of the columns you have and the columns you want,
# yielding the columns you don't have yet
new_col_df = pd.DataFrame(columns=list(set(hosp_wide_feat.values()) - set(df.columns)))
df = df.join(new_col_df)

#####################################################
# FILL COLUMNS THAT SHOULD BE HARD CODED
# this is where you fill in the blanks with the easy
# stuff, like what version of ICD is in the data.
#####################################################

# These are completely dependent on data source
df["representative_id"] = 3  # not representative
df["location_id"] = 91  # portugal

# group_unit 1 signifies age data is in years
df["age_group_unit"] = 1
df["source"] = "PRT_CAHS"  # Central Administration of the Health System

# code 1 for ICD-9, code 2 for ICD-10
df["code_system_id"] = 1  # it's ICD 9

# metric_id == 1 signifies that the 'val' column consists of counts
df["metric_id"] = 1

# Create a dictionary with year-nid as key-value pairs
# nid_dictionary = {'example_year': 'example_nid'}
# df = fill_nid(df, nid_dictionary)
df["nid"] = 285520

df["facility_id"] = "inpatient unknown"

#####################################################
# CLEAN VARIABLES
#####################################################

# Turn 'age' into 'age_start' and 'age_end'
#   - bin into year age ranges
#   - under 1, 1-4, 5-9, 10-14 ...

# FIX AGES
df = df[df["age"] < 125]  # get rid of ages that make no sense
df.loc[df["age"] > 95, "age"] = 95  # this way everything older than GBD
# terminal age start will be lumped into the terminal age group.
df = hosp_prep.age_binning(df, clinical_age_group_set_id=3)
df.drop("age", axis=1, inplace=True)  # changed age_binning to not drop age col


#####################################################
# MANUAL PROCESSING
# this is where fix the quirks of the data, like making values in the
# data match the values we use.

# For example, repalce "Male" with the number 1
#####################################################

# diagnosis id
# data is still stored wide
# df['diagnosis_id'].replace(["P", "S"], [1, 2], inplace=True)

# outcome_id
outcome_dict = {
    0: "unknown",
    1: "discharge",
    2: "discharge",
    6: "discharge",
    7: "discharge",
    13: "discharge",
    20: "death",
    51: "discharge",
    61: "discharge",
    63: "discharge",
}
df["outcome_id"].replace(outcome_dict, inplace=True)


# switch external cause and nature of injury
# this line switches dx_1 and dx_2 where they meet both condtions
# df.loc[df.cod_causa_ext.notnull(), ['cod_diagnostico', 'cod_causa_ext']] =\
#    df.loc[df.cod_causa_ext.notnull(), ['cod_causa_ext', 'cod_diagnostico']].values
df["dx_40"] = np.nan
df.loc[df.ecode_1.notnull(), "dx_40"] = df.loc[df.ecode_1.notnull(), "dx_1"]
df.loc[df.ecode_1.notnull(), "dx_1"] = df.loc[df.ecode_1.notnull(), "ecode_1"]


# Columns contain only 1 optimized data type
int_cols = [
    "year",
    "sex_id",
    "representative_id",
    "code_system_id",
    "age_group_unit",
    "age_group_unit",
    "nid",
    "metric_id",
    "age_start",
    "age_end",
]
# BE CAREFUL WITH NULL VALUES IN THE STRING COLUMNS, they will be converted
# to the string "nan"
# str_cols = ['cod_diagnostico', 'source', 'facility_id', 'outcome_id']
# cast external causes, which have nulls, to string, while preserving nulls
# df['cod_causa_ext'] = df.cod_causa_ext.loc[df.cod_causa_ext.notnull()].map(str)


for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="raise")
# for col in str_cols:
#    df[col] = df[col].astype(str)

# Find all columns with dx_ at the start
diagnosis_feats = df.columns[df.columns.str.startswith("dx_")]
# Remove non-alphanumeric characters from dx feats
for feat in diagnosis_feats:
    df[feat] = hosp_prep.sanitize_diagnoses(df[feat])

# store the data wide for the EN matrix
# drop the ecode_1 col cause it's already in the dx_1 col
df.drop("ecode_1", axis=1, inplace=True)
df.to_stata(r"FILEPATH")


#####################################################
# IF MULTIPLE DX EXIST:
# TRANSFORM FROM WIDE TO LONG
#####################################################

# drop ecodes
e_cols = df.filter(regex="^ecode").columns
df.drop(e_cols, axis=1, inplace=True)
if len(diagnosis_feats) > 1:
    # Reshape diagnoses from wide to long
    #   - review `hosp_prep.py` for additional documentation
    df = hosp_prep.stack_merger(df)

elif len(diagnosis_feats) == 1:
    df.rename(columns={"dx_1": "cause_code"}, inplace=True)
    df["diagnosis_id"] = 1

else:
    print("Something went wrong, there are no ICD code features")

# If individual record: add one case for every diagnosis
df["val"] = 1

# want the stuff that used to be labeled as a secondary diagnosis to continue
# to be labeled as a secondary diagnosis  (stack_merger was not made to be
# used like this)
# df.loc[df.old_diagnosis_id == 2, 'diagnosis_id'] = 2
# df.drop("old_diagnosis_id", axis=1, inplace=True)  # drop old diagnosis id
df.drop("patient_index", axis=1, inplace=True)  # by product we don't need

#####################################################
# GROUPBY AND AGGREGATE
#####################################################

# Check for missing values
print("Are there missing values in any row?\n")
null_condition = df.isnull().values.any()
if null_condition:
    print(">> Yes.  ROWS WITH ANY NULL VALUES WILL BE LOST ENTIRELY")
else:
    print(">> No.")

# still haven't made year_start and year_end
df["year_start"] = df["year"]
df["year_end"] = df["year"]
df.drop("year", axis=1, inplace=True)

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

# convert cause code from unicode to str
df_agg.cause_code = df_agg.cause_code.astype(str)

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
    "number of feature levels age start should match number of feature "
    + r"levels age end"
)
assert (
    len(df_agg["diagnosis_id"].unique()) <= 2
), "diagnosis_id should have 2 or less feature levels"
assert (
    len(df_agg["sex_id"].unique()) == 2
), "There should only be two feature levels to sex_id"
assert (
    len(df_agg["code_system_id"].unique()) <= 2
), "code_system_id should have 2 or less feature levels"
assert len(df_agg["source"].unique()) == 1, "source should only have one feature level"


#####################################################
# COMPARE AGAINST LAST FORMATTED VERSION
#####################################################
base = "FILEPATH"
compare_df = pd.read_hdf((f"FILEPATH"))
compare_df.loc[compare_df["age_start"] == 95, "age_end"] = 125
assert df_agg.val.sum() == compare_df.val.sum()

groups = [
    "age_start",
    "age_end",
    "sex_id",
    "location_id",
    "year_start",
    "diagnosis_id",
]  # , 'cause_code']
a = compare_df.groupby(groups).val.sum().reset_index()
b = df_agg.groupby(groups).val.sum().reset_index()

m = a.merge(b, how="outer", validate="1:1", suffixes=("_old", "_new"), on=groups)
m = m[m.diagnosis_id == 1]
m["new_minus_old"] = m["val_new"] - m["val_old"]
assert (
    abs(m.loc[m["new_minus_old"].notnull(), "new_minus_old"]) < 1
).all(), "large diffs"

#####################################################
# WRITE TO FILE
#####################################################

# Saving the file
write_path = root + r"FILEPATH"

hosp_prep.write_hosp_file(df_agg, write_path, backup=True)

from datetime import datetime

import pandas as pd


def log(location, update_type, message, print_log=False):
    logs = pd.read_pickle("files/logs")
    logs = logs.append(pd.DataFrame({"Date": [datetime.now().replace(microsecond=0)],
                                     "Location": [location],
                                     "Type": [update_type],
                                     "Messsage": [message]}),
                       ignore_index=True)
    logs.to_pickle("files/logs")
    if print_log:
        print("\n", logs.iloc[-1:, :].to_string(index=False, header=False))


def df_selector(df, lower_bound_date=None, upper_bound_date=None, nrows=None, keep=None, exclude=None, drop_dup=False):
    if upper_bound_date is not None:
        df = df.loc[df["Date"] < upper_bound_date, :]

    if lower_bound_date is not None:
        df = df.loc[df["Date"] > lower_bound_date, :]

    if keep is not None and len(keep) > 0:
        to_keep = pd.DataFrame()
        for col, arg in keep.items():
            if not isinstance(arg, list):
                raise TypeError("Keep value be a list")
            to_keep = pd.concat([to_keep, pd.DataFrame(columns=arg)], axis=1)
            for arg_col in arg:
                to_keep[arg_col] = df[col] == arg_col
        df = df.loc[to_keep.any(axis=1), :]

    if exclude is not None and len(exclude) > 0:
        for col, arg in exclude.items():
            if not isinstance(arg, list):
                raise TypeError("Exclude value must be a list")
            for arg_col in arg:
                df = df.loc[df[col] != arg_col, :]

    if nrows is not None and nrows > 0:
        df = df.iloc[-nrows:, :]

    if drop_dup:
        df = df.reset_index(drop=True)
        df = df.loc[:, (df != df.iloc[0]).any()].dropna(how="all", axis=1)

    return df

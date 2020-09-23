def get_histogram(np_array):
    import numpy as np
    import pandas as pd
    np_array_without_nulls = np_array[~pd.isnull(np_array)]
    y, bins = np.histogram(np_array_without_nulls, bins=10)
    return [{"bin_start": bins[i], "bin_end": bins[i + 1], "count": count} for i, count in enumerate(y)]

def get_categories(np_array):
    import numpy as np
    import pandas as pd
    from collections import Counter

    pandas_series = pd.Series(np_array.tolist())
    sum_all = len(pandas_series)

    # special treatment for empty values
    num_nans = pandas_series.isna().sum()

    counter = Counter(pandas_series.dropna().astype(str))

    max_items = 3
    if num_nans > 0:
        max_items -=1 # We need to save space for "missing" category

    if len(counter) > max_items:
        most_common = counter.most_common(max_items - 1)
        counter -= dict(most_common)
        sum_others = sum(counter.values())
        num_others = len(counter)
        most_common.append(("{} others".format(num_others), sum_others))
        categories = most_common
    else:
        categories = counter.most_common(max_items)

    if num_nans > 0:
        categories.append(("Missing", num_nans))

    return [{"name": name, "count": count} for name, count in categories]


# TODO: Get rid of the dependency on unique column names (will require a change in format and not to use .to_dict())
# TODO: Then remove the df.copy() to save memory.
# TODO: Bail early if the dataframe is just too big.
# TODO: Make this work for categorical dataframes
def describe_pd_dataframe(df):
    import math
    import pandas as pd
    import numpy as np

    df_analyzed = df.copy()

    # Make sure the column names are unique since they don't have to be
    df_analyzed.columns = pd.io.parsers.ParserBase({'names': df_analyzed.columns})._maybe_dedup_names(df_analyzed.columns)

    # Analyze only certain number of columns to keep things fast
    max_cells_to_analyze = 100000 # calculated so that the analysis takes no more than 100ms
    if (len(df_analyzed) == 0):
        max_columns_to_analyze = len(df_analyzed.columns)
    else:
        max_columns_to_analyze = min(math.floor(max_cells_to_analyze / len(df_analyzed)), len(df_analyzed.columns))

    # Display only certain number of rows to keep things fast
    max_cells_to_display = 1000
    if (len(df_analyzed.columns) == 0):
        max_rows_to_display = len(df_analyzed)
    else:
        max_rows_to_display = min(math.floor(max_cells_to_display / len(df_analyzed.columns)), len(df_analyzed))

    # We need to send data to frontend in a form of a list, otherwise we loose information
    # on sorting/ordering of the dataframe. However, when we are sending data as list (orient='records')
    # we are loosing the information on index so we need to send it to frontend using a custom column name
    df_analyzed['_deepnote_index_column'] = df_analyzed.index

    if (len(df_analyzed) == max_rows_to_display):
        skip_start = None
        skip_end = None
        df_display_top = df_analyzed.fillna('nan').to_dict(orient='records')
        df_display_bottom = None
    else:
        skip_count = len(df_analyzed) - max_rows_to_display
        skip_start = math.floor((len(df_analyzed) - skip_count) / 2)
        skip_end = skip_start + skip_count
        df_display_top = df_analyzed.iloc[:skip_start].fillna('nan').to_dict(orient='records')
        df_display_bottom = df_analyzed.iloc[skip_end:].fillna('nan').to_dict(orient='records')

    # Analyze columns
    columns = [{ 'name': name } for name in df_analyzed.columns]

    # Add dtypes to columns
    for i, dtype in enumerate(df_analyzed.dtypes):
        columns[i]['dtype'] = str(dtype)

    # Add stats to columns, but only within computational limit
    for i in range(max_columns_to_analyze):
        column = df_analyzed.iloc[:,i] # We need to use iloc because it works if column names have duplicates
        columns[i]['stats'] = {
            'unique_count': column.dropna().nunique(),
            'nan_count': column.isnull().sum(),
        }
        if (np.issubdtype(column.dtype, np.number)):
            columns[i]['stats']['min'] = min(column.dropna()) if len(column.dropna()) > 0 else None
            columns[i]['stats']['max'] = max(column.dropna()) if len(column.dropna()) > 0 else None
            columns[i]['stats']['histogram'] = get_histogram(np.array(column))
        else:
            columns[i]['stats']['categories'] = get_categories(np.array(column))

    return {
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': columns,
        'rows_top': df_display_top,
        'rows_bottom': df_display_bottom,
    }

# TODO: Then remove the series.copy() to save memory.
# TODO: Bail early if the series is just too big.
def describe_pd_series(series):
    import math
    import pandas as pd
    import numpy as np

    series_analyzed = series.copy()

    # Display only certain number of rows to keep things fast
    max_rows_to_display = 1000

    # If the series is categorical, we need to create a category for nan
    if series_analyzed.dtype.name == 'category':
        series_analyzed = series_analyzed.cat.add_categories('nan')

    if (len(series_analyzed) <= max_rows_to_display):
        skip_start = None
        skip_end = None
        series_display_top = series_analyzed.fillna('nan').to_dict()
        series_display_bottom = None
    else:
        skip_count = len(series_analyzed) - max_rows_to_display
        skip_start = math.floor((len(series_analyzed) - skip_count) / 2)
        skip_end = skip_start + skip_count
        series_display_top = series_analyzed.iloc[:skip_start].fillna('nan').to_dict()
        series_display_bottom = series_analyzed.iloc[skip_end:].fillna('nan').to_dict()

    # Analyze columns
    column = {
        'name': series_analyzed.name,
        'dtype': series_analyzed.dtype,
        'stats': {
            'unique_count': series_analyzed.dropna().nunique(),
            'nan_count': series_analyzed.isnull().sum(),
        }
    }

    # Add stats to columns, but only within computational limit
    if (series_analyzed.dtype.name != 'category' and np.issubdtype(series_analyzed.dtype, np.number)):
        column['stats']['min'] = min(series_analyzed.dropna()) if len(series_analyzed.dropna()) > 0 else None
        column['stats']['max'] = max(series_analyzed.dropna()) if len(series_analyzed.dropna()) > 0 else None
        column['stats']['histogram'] = get_histogram(np.array(series_analyzed))
    else:
        column['stats']['categories'] = get_categories(np.array(series_analyzed))

    return {
        'row_count': len(series),
        'column': column,
        'rows_top': series_display_top,
        'rows_bottom': series_display_bottom,
    }

# ! There is an assumption that this file is idempotent - we might run it multiple
# times on the same kernel.

# Deprecated, but we need this until we refactor how variable explorer works.
def _deepnote_get_var_list():
    import json
    from sys import getsizeof
    import numpy as np
    import pandas as pd
    from IPython import get_ipython
    from IPython.core.magics.namespace import NamespaceMagics

    MAX_CONTENT_LENGTH = 500

    _nms = NamespaceMagics()
    _Jupyter = get_ipython()
    _nms.shell = _Jupyter.kernel.shell

    def _getsizeof(x):
        # return the size of variable x. Amended version of sys.getsizeof
        # which also supports ndarray, Series and DataFrame
        try:
            if isinstance(x, (np.ndarray, pd.Series)):
                return x.nbytes
            elif isinstance(x, pd.DataFrame):
                return x.memory_usage().sum()
            else:
                return getsizeof(x)
        except:
            None

    def _getshapeof(x):
        # returns the shape of x if it has one
        # returns None otherwise - might want to return an empty string for an empty collum
        try:
            return x.shape
        except AttributeError:  # x does not have a shape
            return None

    def _getunderlyingdatatype(x):
        # returns the underlying datatype of x if it has one
        # returns None otherwise
        try:
            return x.dtype.name
        except AttributeError:  # x does not have an underlying dtype
            return None

    def _getcontentof(x):
        try:
            if type(x).__name__ == 'DataFrame':
                colnames = ', '.join(x.columns.map(str))
                content = "Column names: %s" % colnames
            elif type(x).__name__ == 'Series':
                content = "Series [%d rows]" % x.shape
            elif type(x).__name__ == 'ndarray':
                content = x.__repr__()
            else:
                if hasattr(x, '__len__') and len(x) > MAX_CONTENT_LENGTH:
                    content = str(x[:MAX_CONTENT_LENGTH]) + "…"
                else:
                    content = str(x)

            if len(content) > MAX_CONTENT_LENGTH:
                return content[:MAX_CONTENT_LENGTH] + "…"
            else:
                return content
        except:
            return None

    def _get_number_of_elements(x):
        try:
            return len(x)
        except:
            return None

    def _get_number_of_columns(x):
        try:
            if isinstance(x, pd.DataFrame):
                return len(x.columns)
            else:
                return None
        except:
            return None

    def to_int(x):
        # for JSON serialization purposes, we need to convert numpy integers to standard integers
        return int(x) if x else None

    def _get_dict_entry(var_name):
        try:
            v = eval(var_name)
            shape = _getshapeof(v)
            underlying_data_type = _getunderlyingdatatype(v)
            return {'varName': var_name,
                    'varType': type(v).__name__,
                    'varSize': to_int(_getsizeof(v)),
                    'varShape': str(shape) if shape else '',
                    'varContent': _getcontentof(v) or '',
                    'varUnderlyingType': str(underlying_data_type) if underlying_data_type else '',
                    'numElements': to_int(_get_number_of_elements(v)),
                    'numColumns': to_int(_get_number_of_columns(v)) }
        except LookupError as e:
            return None

    variables = _nms.who_ls()
    variables = filter(lambda v: v not in ['_html', '_nms', 'NamespaceMagics', '_Jupyter'], variables)
    variables = filter(lambda v: type(eval(v)).__name__ not in ['module', 'function', 'builtin_function_or_method', 'instance', '_Feature', 'type', 'ufunc'], variables)
    variables_dic = {v: _get_dict_entry(v) for v in variables}
    variables_dic = {k: v for k, v in variables_dic.items() if v is not None}

    return json.dumps({'variables': variables_dic})

def _deepnote_get_var_details(target_variable, df_max_rows=100):
    from collections import Counter

    MAX_FREQ_ITEMS = 3
    MAX_DF_COLUMNS = 10

    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        pass

    def _get_column_headers(x):
        stats = _get_descriptive_statistics(x)
        if isinstance(x, (np.ndarray, list)):
            if stats is not None:
                array_header = { 'name': "", 'stats': stats[0] }
                return [array_header]
            else:
                return str([""])
        else:
            return None

    def _get_series_descriptive_statistics(pandas_series):
        series_stats = pandas_series.dropna().infer_objects().describe().dropna().to_dict()
        series_stats['nan_count'] = pandas_series.isnull().sum()
        return series_stats

    def _get_descriptive_statistics(x):
        if isinstance(x, np.ndarray):
            series = pd.Series(x.tolist())
            series_stats = _get_series_descriptive_statistics(series)
            return [series_stats]
        elif isinstance(x, list):
            series = pd.Series(x)
            series_stats = _get_series_descriptive_statistics(series)
            return [series_stats]
        else:
            return None

    def _get_categorical_frequency_data(np_array):
        pandas_series = pd.Series(np_array.tolist())
        sum_all = len(pandas_series)

        # special treatment for empty values
        num_nans = pandas_series.isna().sum()
        has_nans = num_nans > 0

        counter = Counter(pandas_series.dropna().astype(str))

        nonempty_items_to_return = MAX_FREQ_ITEMS - 1 if has_nans else MAX_FREQ_ITEMS

        if len(counter) > nonempty_items_to_return:
            most_common = counter.most_common(nonempty_items_to_return - 1)
            counter -= dict(most_common)
            sum_others = sum(counter.values())
            num_others = len(counter)
            most_common.append(("{} others".format(num_others), sum_others))
            items_with_counts = most_common
        else:
            items_with_counts = counter.most_common(nonempty_items_to_return)

        if has_nans:
            items_with_counts.insert(0, ("Missing", num_nans))

        frequency_rows = [{"name": name, "frequency": count / sum_all} for name, count in items_with_counts]
        type = "freq"
        return frequency_rows, type

    def _get_array_frequency_data(np_array):
        try:
            np_array_without_nulls = np_array[~pd.isnull(np_array)]
            if len(np_array_without_nulls) > 0:
                # we assume the series is a numeric variable, otherwise this throws TypeError
                y, bins = np.histogram(np_array_without_nulls)
                points = [{"x": i, "y": j} for i, j in zip(bins[:-1], y)]
                type = "hist"
                return points, type
            else:
                return _get_categorical_frequency_data(np_array)
        except (TypeError, ValueError):
            # this means the series represents a categorical variable
            return _get_categorical_frequency_data(np_array)

    def _get_frequency_data(x):
        if isinstance(x, (np.ndarray, list)):
            column_data, type = _get_array_frequency_data(np.asarray(x))
            return [{"frequencyData": column_data, "type": type}]
        else:
            return None

    var_details = {
        'dataframe': None,
        'columns': _get_column_headers(target_variable),
        'frequencyInfo': _get_frequency_data(target_variable)}

    return {k: v for k, v in var_details.items() if v is not None}

# Deprecated, but we need this until we refactor how variable explorer works.
def _deepnote_get_var_details_json(var):
    import json
    import numpy as np
    import pandas as pd
    import datetime
    import warnings
    from variable_explorer_helpers import describe_pd_dataframe, describe_pd_series

    class DataEncoder(json.JSONEncoder):
        """ Special json encoder for numpy types """
        def default(self, obj):
            if hasattr(obj, 'to_json'):
                return obj.to_json()
            elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                                np.int16, np.int32, np.int64, np.uint8,
                                np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.bool_)):
                return bool(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32,
                                np.float64)):
                return float(obj)
            elif isinstance(obj, (np.ndarray,)):
                return obj.tolist()
            elif isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
                return obj.isoformat()
            elif isinstance(obj, datetime.timedelta):
                return (datetime.datetime.min + obj).time().isoformat()
            elif isinstance(obj, (pd.DatetimeIndex, )):
                return str(obj)

            try:
                return json.JSONEncoder.default(self, obj)
            except:
                return str(obj)

    # sometimes we get unexpected warnings and we don't want to include those in what we print
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')

        if isinstance(var, pd.DataFrame):
            return json.dumps(describe_pd_dataframe(var), cls=DataEncoder)
        elif isinstance(var, pd.Series):
            return json.dumps(describe_pd_series(var), cls=DataEncoder)
        else:
            return json.dumps(_deepnote_get_var_details(var), cls=DataEncoder)


def _deepnote_add_formatters():
    import traceback
    import pandas as pd
    from IPython import get_ipython
    from variable_explorer_helpers import describe_pd_dataframe

    def dataframe_formatter(df):
        # inspired by https://jupyter.readthedocs.io/en/latest/reference/mimetype.html
        MIME_TYPE = 'application/vnd.deepnote.dataframe.v2+json'
        try:
            return { MIME_TYPE: describe_pd_dataframe(df) }
        except:
            return { MIME_TYPE: { 'error': traceback.format_exc() } }
    get_ipython().display_formatter.mimebundle_formatter.for_type(pd.DataFrame, dataframe_formatter)

if __name__ == '__main__':
    _deepnote_add_formatters()

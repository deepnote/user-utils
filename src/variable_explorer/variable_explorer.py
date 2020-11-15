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

def _deepnote_add_formatters():
    import traceback
    import pandas as pd
    from IPython import get_ipython
    from variable_explorer_helpers import describe_pd_dataframe

    def dataframe_formatter(df):
        # inspired by https://jupyter.readthedocs.io/en/latest/reference/mimetype.html
        MIME_TYPE = 'application/vnd.deepnote.dataframe.v2+json'
        MAX_COLUMNS = 500
        try:
            if (len(df.columns) > MAX_COLUMNS):
                df.drop(df.columns[MAX_COLUMNS:], axis=1, inplace=True)
            return { MIME_TYPE: describe_pd_dataframe(df) }
        except:
            return { MIME_TYPE: { 'error': traceback.format_exc() } }
    get_ipython().display_formatter.mimebundle_formatter.for_type(pd.DataFrame, dataframe_formatter)

if __name__ == '__main__':
    _deepnote_add_formatters()

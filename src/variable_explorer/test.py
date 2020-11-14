import unittest
import pandas as pd
import datetime

from variable_explorer_helpers import describe_pd_dataframe
from variable_explorer import _deepnote_get_var_details_json

class TestDataframeDescribe(unittest.TestCase):
    def test_dataframe(self):
        df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 2)
        self.assertEqual(result['column_count'], 2)
        self.assertEqual(len(result['rows_top']), 2)
        self.assertEqual(result['rows_bottom'], None)
        self.assertEqual(result['columns'][0]['name'], 'col1')

    def test_dataframe_sort(self):
        df = pd.DataFrame(data={'col1': [3, 1, 2]})
        result = describe_pd_dataframe(df.sort_values('col1'))
        self.assertEqual(result['rows_top'][0]['col1'], 1)
        self.assertEqual(result['rows_top'][1]['col1'], 2)
        self.assertEqual(result['rows_top'][2]['col1'], 3)
        # _deepnote_index_column is hidden on frontend. See variable_explorer_helpers for more info.
        self.assertEqual(result['rows_top'][0]['_deepnote_index_column'], 1)

    # TODO: Support non-hashable types like []
    def test_categorical_columns(self):
        df = pd.DataFrame(data={
            'cat1': ['a', 'b', 'c', 'd'],
            'cat2': ['a', 'b', None, 'd'],
            # 'cat3': [1, (2,3), '4', []],
            'cat3': [1, (2,3), '4', 5],
            'cat4': [True, True, True, False],
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 4)
        self.assertEqual(result['column_count'], 4)
        self.assertEqual(len(result['rows_top']), 4)
        self.assertEqual(result['rows_bottom'], None)
        self.assertDictEqual(result['columns'][0], {
            'name': 'cat1',
            'dtype': 'object',
            'stats': {
                'unique_count': 4,
                'nan_count': 0,
                'categories': [
                    {'name': 'a', 'count': 1},
                    {'name': 'b', 'count': 1},
                    {'name': '2 others', 'count': 2},
                ]
            },
        })
        self.assertEqual(result['columns'][1]['stats']['categories'], [
            {'name': 'a', 'count': 1},
            {'name': '2 others', 'count': 2},
            {'name': 'Missing', 'count': 1},
        ])

    # TODO: Support for big ints which can't be converted to float64 and complex numbers
    def test_numerical_columns(self):
        df = pd.DataFrame(data={
            'col1': [1, 2, 3, 4],
            'col2': [1, 2, None, 4],
            # 'col3': [1, 2.1, complex(-1.0, 0.0), 10**1000]
            'col3': [1, 2.1, 3, 4]
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 4)
        self.assertEqual(result['column_count'], 3)
        self.assertEqual(len(result['rows_top']), 4)
        self.assertEqual(result['rows_bottom'], None)
        self.assertEqual(result['columns'][0]['name'], 'col1')

    def test_big_dataframe(self):
        import numpy as np
        df = pd.DataFrame(data={
            'col1': np.arange(100000),
            'col2': np.arange(100000),
            'col3': np.arange(100000),
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 100000)
        self.assertEqual(result['column_count'], 3)
        self.assertEqual(len(result['rows_top']), 166)
        self.assertEqual(len(result['rows_bottom']), 167)
        self.assertTrue('stats' in result['columns'][0])
        self.assertTrue('stats' not in result['columns'][1])

        df = pd.DataFrame(data={
            'col1': np.arange(200000),
            'col2': np.arange(200000),
            'col3': np.arange(200000),
        })
        result = describe_pd_dataframe(df)
        self.assertTrue('stats' not in result['columns'][0])

    def test_no_rows(self):
        df = pd.DataFrame(data={
            'col1': [],
            'col2': [],
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 0)
        self.assertEqual(result['column_count'], 2)

    def test_no_columns(self):
        df = pd.DataFrame(data={})
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 0)
        self.assertEqual(result['column_count'], 0)

    def test_duplicate_columns(self):
        df = pd.DataFrame(data={
            'col1': ['a', 'b', 'c', 'd'],
            'col2': [1, 2, 3, 4],
        })
        df.columns = ['col1', 'col1']
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 4)
        self.assertEqual(result['column_count'], 2)
        self.assertEqual(result['columns'][0]['name'], 'col1')
        self.assertEqual(result['columns'][1]['name'], 'col1.1')

    def test_nans(self):
        df = pd.DataFrame(data={
            'col1': [None, None, None],
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 3)
        self.assertEqual(result['column_count'], 1)
        self.assertEqual(result['columns'][0]['stats'], {
            'unique_count': 0,
            'nan_count': 3,
            'categories': [
                {'name': 'Missing', 'count': 3},
            ]
        })

    def test_datetime(self):
        df = pd.DataFrame(data={
            'col1': [1,2],
            'col2': [datetime.date(2000,1,1), datetime.time(10,30)]
        })
        result = describe_pd_dataframe(df)
        self.assertEqual(result['row_count'], 2)
        self.assertEqual(result['column_count'], 2)

class TestVarDetails(unittest.TestCase):
    def test_get_var_details_json(self):
        import numpy as np
        import pandas as pd

        vars = {
            # Native
            'native_boolean': True,
            'native_null': None,
            'native_int': 5,
            'native_float': 2.0,
            'native_complex': 1+2j,
            'native_list': [1,2,3],
            'native_list_2': [1, 2.2, "3", 4+3j],
            'native_range': range(10),
            'native_tuple': (1,2,3),
            'native_tuple_2': (1, 2.2, "3", 4+3j),
            'native_string': "abc",
            'native_string_multiline': '''
            a
            b
            c
            ''',
            'native_set': {1,2,3},
            'native_frozenset': frozenset({1,2,3}),
            'native_dict': {1: 2, 'key': 'value'},
            'native_bytes': b'bytes',
            'native_bytearray': bytearray(b'.\xf0\xf1\xf2'),
            'native_notimplemented': NotImplemented,

            # Numpy
            'np_bool': np.bool(True),
            'np_byte': np.byte(1),
            'np_ubyte': np.ubyte(1),
            'np_short': np.short(1),
            'np_ushort': np.ushort(1),
            'np_intc': np.intc(1),
            'np_uintc': np.uintc(1),
            'np_int_': np.int_(1),
            'np_uint': np.uint(1),
            'np_longlong': np.longlong(1),
            'np_ulonglong': np.ulonglong(1),
            'np_half': np.half(2.0),
            'np_float16': np.float16(2.0),
            'np_single': np.single(2.0),
            'np_double': np.double(2.0),
            'np_longdouble': np.longdouble(2.0),
            'np_csingle': np.csingle(2.0),
            'np_cdouble': np.cdouble(2.0),
            'np_clongdouble': np.clongdouble(2.0),
            'np_int8': np.int8(1),
            'np_int16': np.int16(1),
            'np_int32': np.int32(1),
            'np_int64': np.int64(1),
            'np_intp': np.intp(1),
            'np_uintp': np.uintp(1),
            'np_float32': np.float32(2.0),
            'np_float64': np.float64(2.0),
            'np_float_': np.float_(2.0),
            'np_complex64': np.complex64(1+2j),
            'np_complex128': np.complex128(1+2j),
            'np_complex_': np.complex_(1+2j),
            'np_array': np.array([1,2,3]),
            # TODO: this throws an error, not sure why?
            # 'np_array_2': np.array([1,2.0,"3",1+1j, (1,2,3), [1,2,3]]),
            'np_array_3': np.array([[ 1.+0.j, 2.+0.j], [ 0.+0.j, 0.+0.j], [ 1.+1.j, 3.+0.j]]),
            'np_zeros': np.zeros((2,3)),
            'np_range': np.arange(10),
            'np_range_2': np.arange(2, 10, dtype=float),
            'np_indices': np.indices((3,3)),

            # Pandas
            'pd_series': pd.Series(np.random.randn(5), index=['a', 'b', 'c', 'd', 'e']),
            # TODO: this throws an error, not sure why?
            # 'pd_series_2': pd.Series(['a', 'b', 'c'], index=['a', 'b', 'c'], dtype="string"),
            # TODO: I can't make this work
            # 'pd_series_date_range': pd.Series(range(3), pd.date_range('20130101', periods=3, tz='UTC')),
            'pd_df': pd.DataFrame(np.random.randn(2, 3), index=[1, 2], columns=['A', 'B', 'C']),
            # TODO: I can't make this work
            # 'pd_df_2': pd.DataFrame(np.random.randn(2, 3), index=pd.date_range('1/1/2000', periods=2), columns=['A', 'B', 'C']),
            'pd_category': pd.Series(["a", "b", "c", "a"], dtype="category"),
            # TODO: I can't make this work
            # 'pd_category_df': pd.DataFrame({"A": ["a", "b", "c", "a"], "B": pd.Series(["a", "b", "c", "a"], dtype="category")}),
            'pd_index': pd.Index([1, 2, 3]),
            'pd_index_2': pd.Index(list('abc')),
            'pd_date_range': pd.date_range('3/6/2012 00:00', periods=15, freq='D'),
            'pd_date_range_tz': pd.date_range('3/6/2012 00:00', periods=3, freq='D', tz='Europe/London'),
            'pd_timestamp': pd.Timestamp('2019-01-01', tz='US/Pacific'),
            'pd_datetime': pd.DataFrame({
                'col1': [1,2],
                'col2': [datetime.date(2000,1,1), datetime.time(10,30)]
            }),
            'pd_datetime_index': pd.DatetimeIndex(['11/06/2011 00:00', '11/06/2011 01:00', '11/06/2011 01:00', '11/06/2011 02:00']),
            'pd_period': pd.Period('2012', freq='A-DEC'),
            'pd_period_range': pd.period_range('1/1/2011', '1/1/2012', freq='M'),
            # TODO: this throws an error, not sure why?
            # 'pd_sparse_array': pd.arrays.SparseArray([1,2,np.nan,4]),
            # TODO: SparseDataFrame is deprecated
            # pd_sparse_df: pd.SparseDataFrame({"A": [0, 1]}),
            'pd_interval': pd.Interval(1, 2),
            'pd_interval_2': pd.Interval(0.5, 1.5),
            'pd_interval_range': pd.interval_range(start=0, periods=5, freq=1.5),
            # TODO: this throws an error, not sure why?
            # 'pd_array_int64': pd.array([1, 2, np.nan], dtype="Int64"),
            # TODO: this throws an error, not sure why?
            # pd_array_boolean = pd.array([True, False, None], dtype="boolean"),
            # pd_array_boolean,
        }

        for key, value in vars.items():
            _deepnote_get_var_details_json(value)

if __name__ == '__main__':
    unittest.main()
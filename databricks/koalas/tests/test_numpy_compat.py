#
# Copyright (C) 2019 Databricks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import numpy as np
import pandas as pd

from databricks import koalas as ks
from databricks.koalas.numpy_compat import unary_np_spark_mappings, binary_np_spark_mappings
from databricks.koalas.testing.utils import ReusedSQLTestCase, SQLTestUtils


class NumPyCompatTest(ReusedSQLTestCase, SQLTestUtils):

    @property
    def pdf(self):
        return pd.DataFrame({
            'a': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'b': [4, 5, 6, 3, 2, 1, 0, 0, 0],
        }, index=[0, 1, 3, 5, 6, 8, 9, 9, 9])

    @property
    def kdf(self):
        return ks.from_pandas(self.pdf)

    def test_np_add_series(self):
        kdf = self.kdf
        pdf = self.pdf
        self.assert_eq(np.add(kdf.a, kdf.b), np.add(pdf.a, pdf.b))

        kdf = self.kdf
        pdf = self.pdf
        self.assert_eq(np.add(kdf.a, 1), np.add(pdf.a, 1))

    def test_np_add_index(self):
        k_index = self.kdf.index
        p_index = self.pdf.index
        self.assert_eq(np.add(k_index, k_index), np.add(p_index, p_index))

    def test_np_unsupported(self):
        kdf = self.kdf
        with self.assertRaisesRegex(NotImplementedError, "Koalas.*not.*support.*sqrt.*"):
            np.sqrt(kdf.a, kdf.b)

    def test_np_spark_compat(self):
        # Use randomly generated dataFrame
        pdf = pd.DataFrame(
            np.random.randint(-100, 100, size=(np.random.randint(100), 2)), columns=['a', 'b'])
        kdf = ks.from_pandas(pdf)

        blacklist = [
            # Koalas does not currently support
            "conj",
            "conjugate",
            "isnat",
            "matmul",
            "frexp",

            # Values are close enough but tests failed.
            "arccos",
            "exp",
            "expm1",
            "log",  # flaky
            "log10",  # flaky
            "log1p",  # flaky
            "modf",
            "floor_divide",  # flaky

            # Results seem inconsistent in a different version of, I (Hyukjin) suspect, PyArrow.
            # From PyArrow 0.15, seems it returns the correct results via PySpark. Probably we
            # can enable it later when Koalas switches to PyArrow 0.15 completely.
            "left_shift",
        ]

        for np_name, spark_func in unary_np_spark_mappings.items():
            np_func = getattr(np, np_name)
            if np_name not in blacklist:
                try:
                    # unary ufunc
                    self.assert_eq(np_func(pdf.a), np_func(kdf.a), almost=True)
                except Exception as e:
                    raise AssertionError("Test in '%s' function was failed." % np_name) from e

        for np_name, spark_func in binary_np_spark_mappings.items():
            np_func = getattr(np, np_name)
            if np_name not in blacklist:
                try:
                    # binary ufunc
                    self.assert_eq(
                        np_func(pdf.a, pdf.b), np_func(kdf.a, kdf.b), almost=True)
                    self.assert_eq(
                        np_func(pdf.a, 1), np_func(kdf.a, 1), almost=True)
                except Exception as e:
                    raise AssertionError("Test in '%s' function was failed." % np_name) from e
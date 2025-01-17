# Copyright 2014 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import pytest

import ibis.config as config
from ibis.tests.expr.mocks import MockConnection


class TestInteractiveUse(unittest.TestCase):
    def setUp(self):
        self.con = MockConnection()

    def test_interactive_execute_on_repr(self):
        table = self.con.table('functional_alltypes')
        expr = table.bigint_col.sum()
        with config.option_context('interactive', True):
            repr(expr)

        assert len(self.con.executed_queries) > 0

    def test_repr_png_is_none_in_interactive(self):
        table = self.con.table('functional_alltypes')

        with config.option_context('interactive', True):
            assert table._repr_png_() is None

    def test_repr_png_is_not_none_in_not_interactive(self):
        pytest.importorskip('ibis.expr.visualize')

        table = self.con.table('functional_alltypes')

        with config.option_context(
            'interactive', False
        ), config.option_context('graphviz_repr', True):
            assert table._repr_png_() is not None

    # XXX This test is failing in the OmniSciDB/Spark build, and working
    # in the rest, even if does not seem to depend on the backend.
    # For some reason in that build the statement does not contain
    # the LIMIT. Xfailing with `strict=False` since in the other backends
    # it does work. See #2337
    @pytest.mark.xfail(
        reason='Not obvious why this is failing for omnisci/spark, and this '
        'was incorrectly skipped until now. Xfailing to restore the CI',
        strict=False,
    )
    def test_default_limit(self):
        table = self.con.table('functional_alltypes')

        with config.option_context('interactive', True):
            repr(table)

        expected = """\
SELECT *
FROM functional_alltypes
LIMIT {}""".format(
            config.options.sql.default_limit
        )

        assert self.con.executed_queries[0] == expected

    def test_respect_set_limit(self):
        table = self.con.table('functional_alltypes').limit(10)

        with config.option_context('interactive', True):
            repr(table)

        expected = """\
SELECT *
FROM functional_alltypes
LIMIT 10"""

        assert self.con.executed_queries[0] == expected

    def test_disable_query_limit(self):
        table = self.con.table('functional_alltypes')

        with config.option_context('interactive', True):
            with config.option_context('sql.default_limit', None):
                repr(table)

        expected = """\
SELECT *
FROM functional_alltypes"""

        assert self.con.executed_queries[0] == expected

    def test_interactive_non_compilable_repr_not_fail(self):
        # #170
        table = self.con.table('functional_alltypes')

        expr = table.string_col.topk(3)

        # it works!
        with config.option_context('interactive', True):
            repr(expr)

    def test_histogram_repr_no_query_execute(self):
        t = self.con.table('functional_alltypes')
        tier = t.double_col.histogram(10).name('bucket')
        expr = t.group_by(tier).size()
        with config.option_context('interactive', True):
            expr._repr()
        assert self.con.executed_queries == []

    def test_compile_no_execute(self):
        t = self.con.table('functional_alltypes')
        t.double_col.sum().compile()
        assert self.con.executed_queries == []

    def test_isin_rule_supressed_exception_repr_not_fail(self):
        with config.option_context('interactive', True):
            t = self.con.table('functional_alltypes')
            bool_clause = t['string_col'].notin(['1', '4', '7'])
            expr = t[bool_clause]['string_col'].value_counts()
            repr(expr)

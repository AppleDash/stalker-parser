import unittest

from stalker_parser import StalkerConfigParser

class TestStalkerConfigParser(unittest.TestCase):
    def setUp(self):
        self._parser = StalkerConfigParser()
        with open('doc/test.cfg', 'r') as fp:
            self._parser.parse(line.strip() for line in fp)
        with open('doc/test2.cfg', 'r') as fp:
            self._parser.parse(line.strip() for line in fp)

    def test_section_existence(self):
        self.assertIn('foo', self._parser.sections)
        self.assertIn('bar', self._parser.sections)
        self.assertIn('baz', self._parser.sections)

    def test_basic_values(self):
        self.assertEqual('hello there fine sir', self._parser.sections['foo']['string'])

    def test_inheritance(self):
        bar = self._parser.sections['bar']
        baz = self._parser.sections['baz']

        self.assertEqual('bar data', bar['bar_data'])
        self.assertEqual('baz data', baz['baz_data'])
        self.assertEqual('this is some data', bar['data'])

        # inherited from bar
        self.assertEqual('bar data', baz['bar_data'])

        # overridden from bar
        self.assertEqual('this is different data', baz['data'])

    def test_unresolved_inheritance(self):
        self.assertEqual(['something_else'], self._parser.unresolved_inheritances['quux'])

    def test_multiple_file_inheritance(self):
        self.assertEqual('hello', self._parser.sections['this will come later']['data'])
        self.assertEqual('goodbye', self._parser.sections['and now for something completely different']['data'])
        self.assertEqual('value', self._parser.sections['this will come later']['parent'])

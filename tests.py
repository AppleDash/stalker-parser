import unittest

from stalker_parser import StalkerConfigParser

class TestStalkerConfigParser(unittest.TestCase):
    def setUp(self):
        self._parser = StalkerConfigParser()
        with open('doc/test.cfg', 'r') as fp:
            self._parser.parse(line.strip() for line in fp)
        with open('doc/test2.cfg', 'r') as fp:
            self._parser.parse(line.strip() for line in fp)

        self._sections = dict(self._parser._sections)

    def test_section_existence(self):
        self.assertIn('foo', self._sections)
        self.assertIn('bar', self._sections)
        self.assertIn('baz', self._sections)

    def test_basic_values(self):
        self.assertEqual('hello there fine sir', self._sections['foo']['string'])

    def test_inheritance(self):
        bar = self._sections['bar']
        baz = self._sections['baz']

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
        self.assertEqual('hello', self._sections['this will come later']['data'])
        self.assertEqual('goodbye', self._sections['and now for something completely different']['data'])
        self.assertEqual('value', self._sections['this will come later']['parent'])

    def test_configparser_compat(self):
        self.assertEqual({'foo', 'bar', 'baz', 'quux', 'and now for something completely different', 'this will come later'}, set(self._parser.sections()))
        self.assertEqual('hello there fine sir', self._parser.get('foo', 'string'))
        self.assertEqual(1, self._parser.getint('foo', 'int'))
        self.assertEqual(2.0, self._parser.getfloat('foo', 'float'))
        self.assertEqual(69, self._parser.getint('foo', 'does not exist!', fallback=69))

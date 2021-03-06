import re
import enum
import codecs
import pprint
import warnings

from collections import defaultdict, OrderedDict

class ParseError(Exception):
    pass

# mode for warning about non-fatal parsing errors
class WarningMode(enum.Enum):
    SILENT = 0  # don't warn at all
    WARN   = 1  # print to the console
    RAISE  = 2  # raise an exception


# this is just a dict wrapper that also has a name attached to it...
class StalkerConfigSection:
    def __init__(self, name):
        self.name = name
        self.data = OrderedDict()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def items(self):
        return self.data.items()

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def __repr__(self):
        return 'ConfigSection(name=' + self.name + ', data=' + repr(dict(self.data)) + ')'

    def __str__(self):
        return repr(self)

    def __iter__(self):
        return iter(self.data)


class StalkerConfigParser:
    COMMENT_CHAR = ';'
    RE_SINGLE_FLOAT = re.compile(r'^[\-0-9.]+$')
    RE_LIST_OF_FLOATS = re.compile(r'^([\-0-9.]+\s*,?\s*)+$')

    def __init__(self, warning_mode=WarningMode.WARN, auto_coerce_values=False):
        self.warning_mode = warning_mode
        self.auto_coerce_values = auto_coerce_values
        self.unresolved_inheritances = defaultdict(list)

        self._sections = OrderedDict()

    # INPUT : iterable of lines in the config file
    # OUTPUT: dict of configuration section names to values
    def parse(self, lines):
        current_section = None

        for index, line in enumerate(map(str.strip, lines)):
            if (not line) or (line[0] == self.COMMENT_CHAR):
                continue

            line_number = index + 1

            if line[0] == '[':
                section_name, section_inheritance = self._parse_section_header(line, line_number)
                if section_name not in self._sections:
                    self._sections[section_name] = StalkerConfigSection(section_name)

                current_section = self._sections[section_name]
                self.unresolved_inheritances[section_name].extend(section_inheritance)
            else:
                if not current_section:
                    raise ParseError('key/value pair encountered before first section (line {}, near "{}")'.format(line_number, line))

                key, val = self._parse_key_value(line)

                if key in current_section:
                    self._warn('duplicate key ' + key + ' in section ' + current_section.name)

                current_section[key] = val

        self._merge_inheritance()

    # these methods are designed to behave exactly like Python's built in configparser

    def sections(self):
        return self._sections.keys()

    def has_option(self, section, option):
        return (section in self._sections) and (option in self._sections[section])

    def get(self, section, option, fallback=None):
        if section not in self._sections:
            return fallback

        return self._sections[section].get(option, fallback)

    def getint(self, section, option, fallback=None):
        return self._generic_get(section, option, fallback, int)

    def getfloat(self, section, option, fallback=None):
        return self._generic_get(section, option, fallback, float)

    def getboolean(self, section, option, fallback=None):
        return self._generic_get(section, option, fallback, self._parse_ini_boolean)

    def _generic_get(self, section, option, fallback, coercer):
        value = self.get(section, option, None)

        if not value:
            return fallback

        return coercer(value.strip())

    def _parse_ini_boolean(self, val):
        if val.lower() in {'1', 'yes', 'true', 'on'}:
            return True
        elif val.lower() in {'0', 'no', 'false', 'off'}:
            return False

        raise ValueError('bad boolean value ' + val)

    def _merge_inheritance(self):
        for child, parents in self.unresolved_inheritances.items():
            for parent in parents:
                if parent not in self._sections:
                    continue

                for key, val in self._sections[parent].items():
                    if key not in self._sections[child]:
                        self._sections[child][key] = val

                # it is now resolved
                self.unresolved_inheritances[child].remove(parent)

    # INPUT : line in config file alleged to be a section [header] possibly [with]:inheritance
    # OUTPUT: tuple of (section name, [list of inherited sections])
    # RAISES: ParseError if we run out of data before we finish parsing the section name
    # NOTES : it is assumed that line at the very least starts with [
    def _parse_section_header(self, line, line_number):
        S_NAME = 0  # parsing the name of the section
        S_NEXT = 1  # done parsing name, expecting inheritance or some such
        S_INHE = 2  # parsing inheritance

        state = S_NAME
        name = ''
        inheritance = ''

        for c in line[1:]:
            if state == S_NAME:
                if c == ']':  # End of section header
                    state = S_NEXT
                    continue
    
                name += c
            elif state == S_NEXT:
                if c == ':':
                    state = S_INHE
                    continue
            elif state == S_INHE:
                if c == self.COMMENT_CHAR:
                    break
    
                inheritance += c

        if state == S_NAME:  # we never finished parsing the name
            raise ParseError('end of line when parsing section header name (line {}, near \"{}\")'.format(line_number, line[1:]))

        return name, [x for x in inheritance.strip().split(',') if x]

    # INPUT : line in config file alleged to be a key = value pair
    # OUTPUT: tuple of parsed (key, value)
    # RAISES: never, I hope 
    def _parse_key_value(self, line):
        parsing_key = True  # True means parsing key, False means parsing value
        key = ''
        val = ''
        for c in line:
            if c == self.COMMENT_CHAR:
                break
    
            if parsing_key:
                if c == '=':  # key = value delimiter
                    parsing_key = False
                else:
                    key += c
            else:
                val += c

        val = val.strip()

        if self.auto_coerce_values:
            val = self._parse_value(val)
    
        return key.strip(), val

    # INPUT  : string containing an alleged value from a key/value pair
    # OUTPUT : parsed value, such as a string, float, list of floats, or something else
    def _parse_value(self, value):
        if self.RE_SINGLE_FLOAT.match(value):
            return float(value)

        if self.RE_LIST_OF_FLOATS.match(value):
            return [float(v.strip()) for v in value.split(',')]

        return value

    def _warn(self, message):
        if self.warning_mode == WarningMode.WARN:
            warnings.warn(message)
        elif self.warning_mode == WarningMode.RAISE:
            raise ParseError('fatal warning encountered: ' + message)


if __name__ == '__main__':
    parser = StalkerConfigParser()

    with codecs.open('/home/appledash/Desktop/w_m4_up.ltx', 'r', encoding='utf-8') as fp:
        parser.parse(line.strip() for line in fp)

    pprint.pprint(dict(parser._sections))

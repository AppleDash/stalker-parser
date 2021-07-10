stalker-parser
==============

My friend wanted to parse the data in files from the bastardized INI files that STALKER uses, or something.

It supports overriding of values using the `[child]:parent` syntax, and supports deferring resolution of these overrides until we actually have the file they exist in.

## Example
```python
import pprint
import stalker_parser

parser = stalker_parser.StalkerConfigParser()

with open('/some/file/path', 'r',) as fp:
    parser.parse(line.strip() for line in fp)

pprint.pprint(parser.sections)
```
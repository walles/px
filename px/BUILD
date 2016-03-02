python_requirements()

python_library(
  name='pxlib',
  sources=globs('*.py'),
)

python_binary(
  name='px',
  dependencies=[
    'px:pxlib',
    'px:docopt'
  ],
  entry_point='px',
)

python_tests(
  name = 'unittests',
  sources = globs('*_test.py'),
  dependencies=[
    'px:pxlib'
  ],
)

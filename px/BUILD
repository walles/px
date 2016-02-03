python_library(
  name='pxlib',
  sources=globs('*.py'),
)

python_binary(
  name='px',
  dependencies=[
    '3rdparty:psutil',
    'px:pxlib'
  ],
  entry_point='px',
)

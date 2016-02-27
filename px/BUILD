python_requirements()

python_library(
  name='pxlib',
  sources=globs('*.py'),
)

python_binary(
  name='px',
  dependencies=[
    'px:psutil',
    'px:pxlib'
  ],
  entry_point='px',
)

from setuptools import find_packages, setup

setup(name='sacred_logs',
      version='0.2.0',
      install_requires=['click', 'matplotlib', 'pandas'],
      packages=find_packages(),
      entry_points="""
      [console_scripts]
      sacredlogs=sacred_logs.cli:cli
      """)

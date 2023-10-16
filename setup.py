from os import path
from codecs import open
from setuptools import setup, find_packages

# get current directory
here = path.abspath(path.dirname(__file__))

# get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# # read the API version from disk
# with open(path.join(here, 'vantage6', 'tools', 'VERSION')) as fp:
#     __version__ = fp.read()

# setup the package
# TODO the ohdsi tools need to be installed in the wrapper
setup(
    name='v6-omop-test',
    version="1.0.0",
    description='vantage6 omop test algorithm',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'vantage6-algorithm-tools',
        'pandas',
	    'ohdsi-database-connector',
	    'ohdsi-circe',
	    'ohdsi-feature-extraction',
	    'ohdsi-cohort-generator',
	    'ohdsi-cohort-diagnostics',
	    'ohdsi-common'
    ]
    # ,
    # extras_require={
    # },
    # package_data={
    #     'vantage6.tools': [
    #         'VERSION'
    #     ],
    # }
)

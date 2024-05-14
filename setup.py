import pathlib
from setuptools import setup
from axon.config import version

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
	name="axon-ECRG",
	version=version,
	description="RPC proxy framework",
	long_description=README,
	long_description_content_type="text/markdown",
	url="https://github.com/DuncanMays/axon-ECRG",
	packages=['axon', 'tests'],
	install_requires=['flask', 'uuid', 'requests', 'aiohttp', 'websockets'],
)


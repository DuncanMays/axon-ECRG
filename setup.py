import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
	name="axon-ECRG",
	version="0.0.0",
	description="Edge computing framework developed and maintained by the Edge Computing Research Group at Queen's University",
	long_description=README,
	long_description_content_type="text/markdown",
	url="https://github.com/DuncanMays/axon-ECRG",
	packages=['axon'],
	install_requires=['flask', 'uuid', 'requests', 'aiohttp', 'codecs'],
)

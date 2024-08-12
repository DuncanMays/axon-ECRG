import pathlib
from setuptools import setup, find_packages
# from axon.config import version

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
	name="axon-ECRG",
	version="0.2.3",
	description="RPC proxy framework",
	long_description=README,
	long_description_content_type="text/markdown",
	url="https://github.com/DuncanMays/axon-ECRG",
	packages=['axon', 'axon.tests', 'axon.HTTP_transport'],
	package_data={'': ['pytest.ini']},
	install_requires=[
		'pytest',
		'pytest-asyncio',
		'flask', 
		'uuid', 
		'urllib3',
		'requests', 
		'aiohttp', 
		'python-socketio[client]', 
		'psutil',
		'cloudpickle'
	],
)


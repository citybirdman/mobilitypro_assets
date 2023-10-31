from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in mobilitypro_assets/__init__.py
from mobilitypro_assets import __version__ as version

setup(
	name="mobilitypro_assets",
	version=version,
	description="Doctypes and custom more reports to deal with in mobility",
	author="Ahmed Zaytoon",
	author_email="citybirdman@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

from setuptools import find_packages, setup

# LOADING DOCUMENTATION
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="iSwitch",
    version="1.0.7",
    packages=find_packages(),
    install_requires=["httpx", "simplejson", "colorlog"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="#Einswilli",
    author_email="einswilligoeh@email.com",
    description="SwitchPay Python SDK for AllDotPy internal use. ",
    url="https://github.com/AllDotPy/iSwitch.git",
)

from setuptools import setup, find_packages

setup(
    name="fructify",
    packages=find_packages(exclude=["tests.*"]),
    test_suite="tests",
)

from setuptools import setup, find_packages

setup(
    name="fructify",
    packages=find_packages(exclude=["tests.*"]),
    install_requires=["blinker~=1.4", "flask~=1.1", "honeycomb-beeline~=2.11"],
    test_suite="tests",
)

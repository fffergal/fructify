from setuptools import setup, find_packages

setup(
    name="fructify",
    packages=find_packages(exclude=["tests.*"]),
    install_requires=[
        "authlib~=0.14",
        "blinker~=1.4",
        "flask~=2.2",
        "honeycomb-beeline~=2.11",
        "psycopg2-binary~=2.8",
        "requests~=2.23",
        "wrapt~=1.12",
    ],
    test_suite="tests",
)

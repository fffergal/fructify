from setuptools import setup, find_packages

setup(
    name="fructify",
    packages=find_packages(exclude=["tests.*"]),
    install_requires=[
        "authlib~=0.14",
        "blinker~=1.4",
        "flask~=3.1",
        "honeycomb-beeline~=2.11",
        "psycopg2-binary~=2.9",
        "requests~=2.23",
        "wrapt~=1.16",
    ],
    test_suite="tests",
)

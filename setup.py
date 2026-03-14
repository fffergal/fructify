from setuptools import setup, find_packages

setup(
    name="fructify",
    packages=find_packages(exclude=["tests.*"]),
    install_requires=[
        "authlib~=1.0",
        "blinker~=1.4",
        "flask~=3.1",
        "opentelemetry-exporter-otlp-proto-http~=1.28",
        "opentelemetry-instrumentation-flask>=0.49b0",
        "opentelemetry-instrumentation-requests>=0.49b0",
        "opentelemetry-sdk~=1.28",
        "psycopg2-binary~=2.9",
        "requests~=2.23",
        "wrapt~=1.16",
    ],
    test_suite="tests",
)

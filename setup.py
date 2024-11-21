from setuptools import setup, find_packages

setup(
    name="AirSpaceSim",
    version="0.1.0",
    author="sankarebarri",
    author_email="sankarebarri_dev@yahoo.com,mathservant@gmail.com",
    description="A modular library for aircraft simulation, airspace and route visualisation, and flight tracking.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sankarebarri/AirSpaceSim",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Licence :: OSI Approved :: MIT Licence",
        "Operating System :: OS Independent"
    ],
    keywords="ATC ATM Airspace FlightRoute",
    python_requires=">=3.7",
    install_requires=[
        "",
        "",
    ],
    include_package_data=True
)
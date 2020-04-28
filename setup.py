import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

with open("version", "r") as file:
    version = file.read().strip()

print
setuptools.setup(
    name="hydro_integrations",
    version=version,
    packages=setuptools.find_packages(include=["hydro_integrations", "hydro_integrations.*"]),
    install_requires=[
        "boto3>=1.12.30",
        "sagemaker>=1.52.1",
    ],
    package_data={
        'hydro_integrations': [
            'aws/sagemaker/traffic_shadowing/template.yaml',
        ],
    },
    author="Hydrospheredata",
    author_email="info@hydrosphere.io",
    description="HydroSDK integrations",
    keywords="hydrosphere hydro serving monitoring sagemaker integrations",
    url="https://hydrosphere.io/",

    long_description=long_description,
    long_description_content_type="text/markdown",

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

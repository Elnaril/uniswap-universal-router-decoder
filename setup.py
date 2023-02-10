from setuptools import find_packages, setup

with open('README.md') as readme_file:
    long_description = readme_file.read()

setup(
    name='Uniswap Universal Router Decoder',
    version='0.1.0',
    description='Decode transaction sent to Uniswap universal router',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='elnaril',
    author_email='elnaril_dev@caramail.com',
    packages=find_packages(exclude=["tests", "tests.*", "notes", "notes.*", "virtualenv", "virtualenv.*", ]),
    install_requires=['web3', ],
    python_requires='>=3.8, <4',
    license="MIT",
    keywords="ethereum uniswap universal router decoder",
)

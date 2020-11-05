from setuptools import find_packages, setup

setup(
    name='fourlang',
    version='0.1',
    description='Tools for constructing fourlang graphs',
    url='https://github.com/adaamko/wikt2def',
    author=',Adam Kovacs, Kinga Gemes, Gabor Recski',
    author_email='gabor.recski@tuwien.ac.at,adam.kovacs@tuwien.ac.at, kinga.gemes@tuwien.ac.at',
    license='MIT',
    install_requires=[
        "streamlit",
        "flask",
        "networkx",
        "stanza",
        "nltk",
        "graphviz",
        "sklearn",
        "pandas",
        "requests"
    ],
    packages=find_packages(),
    zip_safe=False)
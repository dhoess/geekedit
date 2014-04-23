from setuptools import find_packages, setup

setup(
    name = 'G.E.E.K.Edit', version = '0.1',
    packages= find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        geekedit = geekedit
    """,
)

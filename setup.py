import os
import setuptools

base_dir = os.path.dirname(__file__)

with open(os.path.join(base_dir, 'README.md')) as f:
    long_description = f.read()

setuptools.setup(
    name='ntext',
    version='0.0.1',
    author='Gabriel Peña',
    author_email='gabriel@mc2.pw',
    license='MIT',
    description='Data structure for representing string diagrams',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mc2pw/ntext',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'hypothesis',
    ],
    include_package_data=True,
    zip_safe=False,
)

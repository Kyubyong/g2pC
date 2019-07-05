import setuptools

with open("README.md", mode="r", encoding="utf-8") as fh:
    long_description = fh.read()

REQUIRED_PACKAGES = [
    'pkuseg>=0.0.22',
    'sklearn_crfsuite>=0.3.6',
]

setuptools.setup(
    name="g2pC",
    version="0.9.4",
    author="Kyubyong Park",
    author_email="kbpark.linguist@gmail.com",
    description="g2pC: A Context-aware g2p module for Chinese",
    install_requires=REQUIRED_PACKAGES,
    license='Apache License 2.0',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kyubyong/g2pC",
    packages=setuptools.find_packages(),
    package_data={'g2pc': ['g2pc/cedict.pkl', 'g2pc/crf100.bin']},
    python_requires=">=3.6",
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
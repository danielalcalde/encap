import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='encap',
     version='0.1.0',
     scripts=['encap', "etool"] ,
     author="Daniel Alcalde Puente",
     author_email="d.alcalde.puente@fz-juelich.de",
     description="A versioning tool for scientific computing experiments.",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/danielalcalde/encap",
     packages=["encap_lib"],
     license="MIT",
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
     ],
     install_requires=["pyyaml>=5.1", "fabric", "GitPython", "psutil"],
 )

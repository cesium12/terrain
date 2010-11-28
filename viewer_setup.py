from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    name="Viewer",
    ext_modules=[
        Extension("viewer", [ "viewer.c" ], libraries=[ 'glut', 'GL', 'GLU' ])
    ],
    cmdclass={ 'build_ext' : build_ext }
)

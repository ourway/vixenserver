#!/bin/bash
source pyenv/bin/activate
WEB2PYPATH=/home/farsheed/Documents/web2py/
cd $WEB2PYPATH
python -OO web2py.py --nogui -a "<recycle>"

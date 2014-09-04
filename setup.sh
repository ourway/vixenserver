#!/bin/bash
sudo apt-get install libxml2-dev libxslt-dev python-dev lib32z1-dev zlib1g-dev
virtualenv pyenv
source pyenv/bin/activate
echo '*' > pyenv/.gitignore
pip install -r reqirements.txt

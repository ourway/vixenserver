#!/bin/bash
virtualenv pyenv
source pyenv/bin/activate
echo '*' > pyenv/.gitignore
pip install -r reqirements.txt

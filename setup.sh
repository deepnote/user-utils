#!/bin/bash
set -euxo pipefail

cd "$(dirname "$0")"

# Configs
cp ./src/ipython/ipython_config.py $HOME/.ipython/profile_default/
cp ./src/jupyter/jupyter_notebook_config.py $HOME/.jupyter/

# Code
mkdir $HOME/.deepnote
cp ./src/ipython/set_notebook_path.py $HOME/.deepnote
cp ./src/variable_explorer/variable_explorer.py $HOME/.deepnote
cp ./src/variable_explorer/variable_explorer_helpers.py $HOME/.deepnote

# Append to .bashrc
echo "
cd ~/work
source /opt/venv/bin/activate
PS1=\"${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@deepnote\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\] \$ \"" >> $HOME/.bashrc



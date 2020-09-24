#!/bin/bash
set -euxo pipefail

cd "$(dirname "$0")"
# Configs
cp ./user-utils/src/ipython/ipython_config.py $HOME/.ipython/profile_default/
cp ./user-utils/src/jupyter/ipython_config.py $HOME/.jupyter/

# Code
mkdir $HOME/.deepnote
cp ./user-utils/src/jupyter/set_notebook_path.py $HOME/.deepnote
cp ./user-utils/src/df/test.py $HOME/.deepnote
cp ./user-utils/src/variable_explorer/variable_explorer.py $HOME/.deepnote
cp ./user-utils/src/variable_explorer/variable_explorer_helpers.py $HOME/.deepnote

# Append to .bashrc
echo 'cd ~/work \n \
    source /opt/venv/bin/activate \n \
    PS1="${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@deepnote\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\] \$ "' >> $HOME/.bashrc

# Get available kernels
jupyter kernelspec list --json | jq -r '.kernelspecs | keys[]' > $HOME/work/.deepnote/available-kernels.txt



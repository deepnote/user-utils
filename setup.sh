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






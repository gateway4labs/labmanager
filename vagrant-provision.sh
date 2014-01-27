#!/usr/bin/env bash

# weblabdeusto
echo 'Provisioning from script'

export SHARED_DIR='/labmanager/'
export ENV_NAME='labmanager_env'

. "/etc/bash_completion.d/virtualenvwrapper"
if [ ! -d /home/vagrant/.virtualenvs/$ENV_NAME ]; then
  mkvirtualenv $ENV_NAME
  workon $ENV_NAME
  pip install $SHARED_DIR
  echo 'Finishing provisioning' $ENV_NAME
else
  echo 'Ignoring existing default environment' $ENV_NAME
fi

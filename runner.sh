#!/bin/bash

get_env() {
  if [ -d ".env" ]; then
    get_activate ".env"
  elif [ -d ".venv" ]; then
    get_activate ".venv"
  else
    echo "Python env not found in $(pwd)"
  fi
}

get_activate() {
  if [ -f "$1/bin/activate" ]; then
    source "$1/bin/activate"
  else
    echo "Activate script not found in $1"
  fi
}

get_env

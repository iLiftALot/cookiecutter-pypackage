#!/bin/zsh

# Set env variables:
#   PROJECT_DIR - The directory of the generated project
#   COOKIECUTTER_CONFIG - The path to the cookiecutter configuration directory
#
# Example alias to set within your shell config (e.g. .zshrc)
# for easy access to the cookiecutter template:
#   alias cookiecutter-python='\
#   cd "$PROJECT_DIR" && \
#   cookiecutter "${COOKIECUTTER_CONFIG:h}/cookiecutter-pypackage"'
#
# The above allows you to run cookiecutter from the anywhere within the CLI.

log() {
  RED='\x1b[1;31m'
  GREEN='\x1b[1;32m'
  YELLOW='\x1b[1;33m'
  BOLD='\x1b[1m'
  UNDERLINE='\x1b[4m'
  RESET='\x1b[0m'

  # Call example: log "this is a message: " "yellow" "this is a value" "bold" "green"
  # Color/style keywords apply to the text segment immediately before them.
  local message=""
  local current_text=""
  local colors=""
  local arg
  for arg in "$@"; do
    case "$arg" in
      "red") colors+="$RED" ;;
      "green") colors+="$GREEN" ;;
      "yellow") colors+="$YELLOW" ;;
      "bold") colors+="$BOLD" ;;
      "underline") colors+="$UNDERLINE" ;;
      *)
        # Flush the previous text segment with any accumulated colors
        if [ -n "$current_text" ]; then
          if [ -n "$colors" ]; then
            message+="${colors}${current_text}${RESET}"
          else
            message+="$current_text"
          fi
        fi
        current_text="$arg"
        colors=""
        ;;
    esac
  done
  # Flush the last text segment
  if [ -n "$current_text" ]; then
    if [ -n "$colors" ]; then
      message+="${colors}${current_text}${RESET}"
    else
      message+="$current_text"
    fi
  fi
  echo -e "$message"
}

log "Starting pre-prompt hook..." "yellow"

# Activate the venv so Jinja2 extensions are importable
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    log "Activated venv: " "yellow" "${SCRIPT_DIR:t}/.venv" "bold" "underline" "green"
else
    log "Error: " "red" "bold" "underline" "Virtual environment not found at ${SCRIPT_DIR:t}/.venv" "red"
    exit 1
fi

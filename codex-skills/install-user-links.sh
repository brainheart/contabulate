#!/bin/sh
set -eu

skills_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
user_skill_root="${HOME}/.agents/skills"

mkdir -p "$user_skill_root"

install_link() {
  skill_name=$1
  target="$skills_root/$skill_name"
  link="$user_skill_root/$skill_name"

  if [ -L "$link" ]; then
    current_target=$(readlink "$link")
    if [ "$current_target" = "$target" ]; then
      printf '%s\n' "Already installed: $skill_name"
      return
    fi
    printf '%s\n' "Refusing to replace existing symlink: $link -> $current_target" >&2
    exit 1
  fi

  if [ -e "$link" ]; then
    printf '%s\n' "Refusing to replace existing path: $link" >&2
    exit 1
  fi

  ln -s "$target" "$link"
  printf '%s\n' "Installed: $skill_name -> $target"
}

install_link contabulate-instances
install_link contabulate-style-tables

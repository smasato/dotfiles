#!/opt/homebrew/bin/zsh

# bat is mise-managed, so resolve it through mise rather than the inherited
# PATH: on a fresh machine the first `chezmoi apply` runs from a shell that
# predates `mise activate`.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "${HOME}"
eval "$(mise env -s zsh)"

bat cache --build

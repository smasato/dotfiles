local wezterm = require 'wezterm'

local config = {}

if wezterm.config_builder then
  config = wezterm.config_builder()
end

config.color_scheme = 'nord'

config.font = wezterm.font('M+1Code Nerd Font')

return config

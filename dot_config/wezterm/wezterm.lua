local wezterm = require 'wezterm'
local config = {}

-- Hyperlink
config.hyperlink_rules = wezterm.default_hyperlink_rules()

-- Appearance
config.color_scheme = 'nord'
config.font = wezterm.font('M+1Code Nerd Font')
config.window_background_opacity = 0.9

-- Window
config.window_close_confirmation = 'NeverPrompt'
config.window_padding = {
  left = 0,
  right = 0,
  top = 0,
  bottom = 0,
}
config.window_decorations = "RESIZE"
config.window_frame = {
  border_left_width = '0cell',
  border_right_width = '0cell',
  border_bottom_height = '0cell',
  border_top_height = '0cell',
}
if wezterm.target_triple == "x86_64-apple-darwin" or wezterm.target_triple == "aarch64-apple-darwin" then
  config.native_macos_fullscreen_mode = true
  config.macos_window_background_blur = 0
end

-- Scroll Bar
config.enable_scroll_bar = false

-- Tab Bar
config.use_fancy_tab_bar = false
config.hide_tab_bar_if_only_one_tab = true

return config

local wezterm = require 'wezterm'
local config = {}

-- functions
local function move_pane(key, direction)
  return {
    key = key,
    mods = 'LEADER',
    action = wezterm.action.ActivatePaneDirection(direction),
  }
end

local function resize_pane(key, direction)
  return {
    key = key,
    action = wezterm.action.AdjustPaneSize { direction, 3 }
  }
end

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
  font = wezterm.font('M+1Code Nerd Font'),
  font_size = 11,
  border_left_width = '0cell',
  border_right_width = '0cell',
  border_bottom_height = '0cell',
  border_top_height = '0cell',
}
config.native_macos_fullscreen_mode = true
config.macos_window_background_blur = 30

-- Scroll Bar
config.enable_scroll_bar = false

-- Keybinds
config.leader = { key = 's', mods = 'CTRL', timeout_milliseconds = 1000 }
config.keys = {
  {
    key = '"',
    mods = 'LEADER',
    action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' },
  },
  {
    key = '%',
    mods = 'LEADER',
    action = wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' },
  },
  {
    key = 'r',
    mods = 'LEADER',
    action = wezterm.action.ActivateKeyTable { name = 'resize_panes', one_shot = false, timeout_milliseconds = 1000 },
  },
  move_pane('j', 'Down'),
  move_pane('k', 'Up'),
  move_pane('h', 'Left'),
  move_pane('l', 'Right'),
}
config.key_tables = {
  resize_panes = {
    resize_pane('j', 'Down'),
    resize_pane('k', 'Up'),
    resize_pane('h', 'Left'),
    resize_pane('l', 'Right'),
  },
}

local appearance = wezterm.gui.get_appearance()

local function segments_for_right_status()
  return {
    wezterm.strftime('%Y-%m-%d'),
    wezterm.strftime('%H:%M'),
    wezterm.hostname(),
  }
end

wezterm.on('update-status', function(window, pane)
  local SOLID_LEFT_ARROW = utf8.char(0xe0b2)
  local segments = segments_for_right_status()

  local color_scheme = window:effective_config().color_scheme
  local palette = wezterm.color.get_builtin_schemes()[color_scheme]
  local bg = wezterm.color.parse(palette.background)
  local fg = palette.foreground

  local gradient_to, gradient_from = bg, bg
  if appearance:find('Dark') then
    gradient_from = gradient_from:lighten(0.2)
  else
    gradient_from = gradient_from:darken(0.2)
  end

  local gradient = wezterm.color.gradient(
    {
      orientation = 'Horizontal',
      colors = { gradient_from, gradient_to },
    },
    #segments -- only gives us as many colours as we have segments.
  )

  local elements = {}

  for i, seg in ipairs(segments) do
    local is_first = i == 1

    if is_first then
      table.insert(elements, { Background = { Color = 'none' } })
    end
    table.insert(elements, { Foreground = { Color = gradient[i] } })
    table.insert(elements, { Text = SOLID_LEFT_ARROW })

    table.insert(elements, { Foreground = { Color = fg } })
    table.insert(elements, { Background = { Color = gradient[i] } })
    table.insert(elements, { Text = ' ' .. seg .. ' ' })
  end

  window:set_right_status(wezterm.format(elements))
end)

return config
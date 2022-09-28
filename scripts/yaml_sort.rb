# frozen_string_literal: true

require 'yaml'
require 'pathname'

yaml = YAML.safe_load(File.open(File.expand_path(ARGV[0]), 'r'))

output = {
  'taps' => yaml['taps'].nil? ? nil : yaml['taps'].sort!,
  'brews' => yaml['brews']&.sort.to_h,
  'casks' => yaml['casks']&.sort.to_a
}

YAML.dump(output, File.open(File.expand_path(ARGV[0]), 'w'))

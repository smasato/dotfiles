# frozen_string_literal: true

require 'yaml'

system('brew bundle dump -f')

brewfile = File.read('Brewfile')

taps = brewfile.scan(/^tap.*$/)
taps.map { |tap| tap.gsub!(/^tap\s+|"/, '') }.sort!

brews = brewfile.scan(/^brew.*$/)
brews.map! { |brew| brew.gsub!(/^brew\s+/, '')&.split(/,/, 2) }

brews_hash = {}

brews.each do |brew|
  if brew.count != 1
    brews_hash[brew[0]&.gsub!(/^"|"?$/, '')] = eval("{#{brew[1]}}").transform_keys(&:to_s)
  else
    brews_hash.store(brew[0]&.gsub!(/^"|"?$/, ''), nil)
  end
end

casks = brewfile.scan(/^cask.*$/)
casks.map! { |cask| cask.gsub!(/^cask\s+|"/, '') }.sort!

output = {
  'taps' => taps,
  'brews' => brews_hash.sort.to_h,
  'casks' => casks
}

YAML.dump(output, File.open('brew.yml', 'w'))

system('rm Brewfile')

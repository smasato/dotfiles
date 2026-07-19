# frozen_string_literal: true

# Sorts package entries in .chezmoidata/packages.yaml.
# For each profile (base/personal/work) under taps/brews/casks, sorts the
# entries alphabetically, keeping nested values (e.g. restart_service: true)
# attached to their entry. packages.yaml is expected to contain no comments.

path = File.expand_path(ARGV[0])
lines = File.readlines(path)

def entry_key(entry)
  entry.first.strip.sub(/\A- /, '').sub(/:\z/, '')
end

output = []
i = 0
while i < lines.size
  line = lines[i]
  output << line
  i += 1

  # Profile key (e.g. "      base:") directly under taps/brews/casks;
  # inline values like "base: []" are left as-is.
  next unless line.match?(/\A {6}[\w-]+:\s*\z/)
  section = output.reverse_each.find { |l| l.match?(/\A {4}\S/) }
  next unless section&.match?(/\A {4}(taps|brews|casks):/)

  entries = []
  while i < lines.size && lines[i].match?(/\A {8}/)
    if lines[i].match?(/\A {8}\S/)
      entries << [lines[i]]
    else
      # Deeper-indented continuation of the current entry.
      entries.last << lines[i]
    end
    i += 1
  end

  output.concat(entries.sort_by { |entry| entry_key(entry) }.flatten)
end

File.write(path, output.join)

#!/usr/bin/env ruby

Dir.glob('defaults/config/**/*').each do |file|
  next if File.directory?(file)
  puts "******** #{file} ******"
  data = open(file).read
  data.gsub!('@{HOME}/php', '@{DEPS_DIR}/{{.DepsIdx}}/php')
  data.gsub!('@{HOME}/nginx', '@{DEPS_DIR}/{{.DepsIdx}}/nginx')
  open(file, 'w') { |f| f.write(data) }
end

## Convert templates
# Dir.glob('defaults/config/**/*').each do |file|
#   next if File.directory?(file)
#   puts "******** #{file} ******"
#   data = open(file).read
#   # data.scan(/(#\{.+?\})+/).each do |m|
#   #   puts "  #{m}"
#   # end
#   data.gsub!(/#\{(.+?)\}/) do
#     k = Regexp.last_match[1]
#     k = k.split('_').collect(&:capitalize).join
#     "{{.#{k}}}"
#   end
#   open(file, 'w') { |f| f.write(data) }
# end


$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Options.JSON' do
  let(:options) { JSON.parse(File.read('defaults/options.json')) }
  let(:manifest) { YAML.load_file('manifest.yml') }
  let(:versions) { manifest['dependencies'].select{|x|x['name']=='php'}.map{|x|Gem::Version.new x['version']}.sort.map(&:to_s) }

  it 'PHP_55_LATEST has the latest 5.5 version' do
    latest = versions.select{|x|x.start_with?('5.5.')}.last
    expect(options['PHP_55_LATEST']).to eq(latest)
  end

  it 'PHP_56_LATEST has the latest 5.6 version' do
    latest = versions.select{|x|x.start_with?('5.6.')}.last
    expect(options['PHP_56_LATEST']).to eq(latest)
  end

  it 'PHP_70_LATEST has the latest 7.0 version' do
    latest = versions.select{|x|x.start_with?('7.0.')}.last
    expect(options['PHP_70_LATEST']).to eq(latest)
  end

  it 'PHP_71_LATEST has the latest 7.1 version' do
    latest = versions.select{|x|x.start_with?('7.1.')}.last
    expect(options['PHP_71_LATEST']).to eq(latest)
  end
end

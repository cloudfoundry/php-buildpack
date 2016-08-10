$: << 'cf_spec'
require 'cf_spec_helper'
require 'yaml'

php_buildpack_manifest_file = File.join(File.expand_path(File.dirname(__FILE__)), '..', '..', 'manifest.yml')
manifest = YAML.load(File.read(php_buildpack_manifest_file))
php_version_5 = manifest['dependencies'].select { |dependency| dependency['name'] == "php" && dependency['version'].to_s[0] == '5' }.first
php_version_7 = manifest['dependencies'].select { |dependency| dependency['name'] == "php" && dependency['version'].to_s[0] == '7' }.first

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }

  before do
    @app = Machete.deploy_app(
      app_name,
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
   # Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP5 app that loads all prepackaged extensions' do
    let(:app_name) { 'php_5_app_with_all_modules' }

    it 'logs each module on the info page' do
      expect(@app).to be_running
      browser.visit_path('/')
      php_version_5['modules'].each do |module_name|
        expect(browser).to have_body Regexp.new("module_#{module_name}", Regexp::IGNORECASE)
      end
    end
  end

  context 'deploying a basic PHP7 app that loads all prepackaged extensions' do
    let(:app_name) { 'php_7_app_with_all_modules' }

    it 'logs each module on the info page' do
      expect(@app).to be_running
      browser.visit_path('/')
      php_version_7['modules'].each do |module_name|
        expect(browser).to have_body Regexp.new("module_#{module_name}", Regexp::IGNORECASE)
      end
    end
  end
end

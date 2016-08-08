$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }
  let(:options_php7_version) do
    defaults_file_path = File.join(File.dirname(__FILE__), '..', '..', 'defaults', 'options.json')
    JSON.parse(File.read(defaults_file_path))["PHP_70_LATEST"]
  end

  before(:context) { @app_name = 'php_app_using_php_7_latest' }

  context 'deploying a basic PHP app using the latest PHP7' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'installs the latest version of PHP7' do
      expect(@app).to have_logged 'Installing PHP'
      expect(@app).to have_logged "PHP #{options_php7_version}"
    end
  end
end


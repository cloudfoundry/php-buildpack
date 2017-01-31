$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'php_app_httpd_custom_modules_conf'}

  context 'deploying a basic PHP app using httpd as the webserver and a custom httpd-modules.conf ' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'compiles and starts the app' do
      expect(@app).to be_running
    end

    it 'does not log an error about the RequestHeader command' do
      expect(@app).not_to have_logged /Invalid command 'RequestHeader'/
    end
  end
end


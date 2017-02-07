$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'php_app_with_logs_dir'}

  context 'app has a logs directory' do
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

    it 'expects the app to respond to GET request' do
      browser.visit_path('/')
      expect(browser).to have_body 'Hello, world'
    end
  end
end



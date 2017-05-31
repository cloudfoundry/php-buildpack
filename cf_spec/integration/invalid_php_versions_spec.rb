$: << 'cf_spec'
require 'cf_spec_helper'

describe 'invalid PHP versions' do
  let(:browser)  { Machete::Browser.new(@app) }
  let(:app_name) { 'invalid_php_version' }

  before do
    @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    @app = deploy_app(app_name, @env_config)
  end

  after do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'version is specified using .bp-config/options.json' do
    it 'logs that an invalid version was provided' do
      expect(@app).to have_logged /WARNING: PHP version 7.34.5 not available, using default version \(5\.6\.\d+\)/
    end

    it 'uses the default PHP version' do
      expect(@app).to have_logged "PHP 5.6"
    end

    it 'stages successfully' do
      expect(@app).to be_running
      browser.visit_path('/')
      expect(browser).to have_body /PHP Version 5.6/
    end
  end

  context 'version is specified using composer.json' do
    let(:app_name) { 'invalid_php_version_composer' }

    it 'logs that an invalid version was provided' do
      expect(@app).to have_logged /WARNING: PHP version >=9.7.0 not available, using default version \(5\.6\.\d+\)/
    end

    it 'uses the default PHP version' do
      expect(@app).to have_logged "PHP 5.6"
    end

    it 'does not stage successfully' do
      expect(@app).not_to be_running
    end
  end
end


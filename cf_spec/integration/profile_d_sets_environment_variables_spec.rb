$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a PHP app with .profile.d directory' do
    let(:app_name) { 'php_app_with_profile_d' }

    it "sets environment variables via .profile.d script" do
      browser.visit_path('/')
      expect(browser).to have_body('TEST_ENV_VAR')
    end
  end

  context 'deploying a PHP app with .profile script' do
    let(:app_name) { 'php_app_with_profile_script' }

    it "sets environment variables via .profile script" do
      cf_api_output = Machete::CF::API.new.execute

      cf_api_version = cf_api_output.match( /API version: (?<version_number>\d+\.\d+\.\d+)/ )['version_number']
      minimum_acceptable_cf_api_version = Gem::Version.new('2.57.0')
      skip(".profile script functionality not supported before CF API version #{minimum_acceptable_cf_api_version}") if Gem::Version.new(cf_api_version) < minimum_acceptable_cf_api_version
      browser.visit_path('/')
      expect(browser).to have_body('PROFILE_SCRIPT_IS_PRESENT_AND_RAN')
    end
  end
end

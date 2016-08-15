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

    before do
      minimum_acceptable_cf_api_version = '2.57.0'
      skip_reason = ".profile script functionality not supported before CF API version #{minimum_acceptable_cf_api_version}"
      Machete::RSpecHelpers.skip_if_cf_api_below(version: minimum_acceptable_cf_api_version, reason: skip_reason)
    end

    it "sets environment variables via .profile script" do
      browser.visit_path('/')
      expect(browser).to have_body('PROFILE_SCRIPT_IS_PRESENT_AND_RAN')
    end

    it 'does not let me view the .profile script' do
      browser.visit_path('/.profile')
      expect(browser.status).to eq(404)
    end
  end
end

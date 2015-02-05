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
      expect(browser).to have_body('HTTPD_SERVER_ADMIN')
    end
  end
end

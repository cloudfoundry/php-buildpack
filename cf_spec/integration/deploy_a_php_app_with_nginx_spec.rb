$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic PHP app using Nginx as the webserver' do
    let(:app_name) { 'php_app_using_nginx' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged '-------> Buildpack version 3'
      expect(app).to have_logged 'Installing Nginx'
      expect(app).to have_logged 'Installing PHP'
      expect(app).to have_logged 'PHP 5.5'

      browser.visit_path('/')
      expect(browser).to have_body('PHP Version')

      assert_cached_mode_has_no_internet_traffic
    end
  end
end


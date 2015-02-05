$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic HHVM app' do
    let(:app_name) { 'hhvm_app' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged 'Installing HHVM'
      expect(app).to have_logged 'HHVM 3.2'

      browser.visit_path('/')
      expect(browser).to have_body('HipHop')
      expect(browser).to have_body('Expect .profile.d to set HTTPD_SERVER_ADMIN=admin@localhost')

      assert_offline_mode_has_no_internet_traffic
    end
  end

  context 'deploying a basic HHVM app with runtime defined in composer.json' do
    let(:app_name) { 'composer_hhvm_app' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged 'Installing HHVM'
      expect(app).to have_logged 'HHVM 3.2'

      browser.visit_path('/')
      expect(browser).to have_body('HipHop')

      assert_offline_mode_has_no_internet_traffic
    end
  end
end



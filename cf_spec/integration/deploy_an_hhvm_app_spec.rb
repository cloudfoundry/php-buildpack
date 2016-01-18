$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }

  after do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic HHVM app' do
    before(:all) do
      @app = Machete.deploy_app('hhvm_app')
    end

    specify do
      expect(@app).to be_running

      expect(@app).to have_logged 'Installing HHVM'

      browser.visit_path('/')
      expect(browser).to have_body('HipHop')
      expect(browser).to have_body('Expect .profile.d to set HTTPD_SERVER_ADMIN=admin@localhost')
    end

    context 'in offline mode', :cached do
      specify { expect(@app).not_to have_internet_traffic }
    end
  end

  context 'deploying a basic HHVM app with runtime defined in composer.json' do
    before(:all) do
      @app = Machete.deploy_app('composer_hhvm_app')
    end

    specify do
      expect(@app).to be_running

      expect(@app).to have_logged 'Installing HHVM'

      browser.visit_path('/')
      expect(browser).to have_body('HipHop')
    end

    context 'in offline mode', :cached do
      specify { expect(@app).not_to have_internet_traffic }
    end
  end
end



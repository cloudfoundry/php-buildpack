$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic PHP app' do
    let(:app_name) { 'php_app' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged '-------> Buildpack version 3'
      expect(app).to have_logged 'Installing PHP'
      expect(app).to have_logged 'PHP 5.4.36'

      browser.visit_path('/')
      expect(browser).to have_body('Hello world!')
    end
  end
end


$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'php_app_testing_locale'
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'the application should run and emit the translated string' do
    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'expects the app to respond to GET request' do
      browser.visit_path('/')
      expect(browser).to have_body 'Hello, world'
    end
  end
end



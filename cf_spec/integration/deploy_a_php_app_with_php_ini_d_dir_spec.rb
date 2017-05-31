$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) do
    Machete.deploy_app(app_name)
  end
  let(:browser)  { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic PHP5 app with custom conf files in php.ini.d dir in app root' do
    let(:app_name) { 'php_5_with_php_ini_d' }

    it 'sets custom configurations' do
      expect(app).to be_running
      browser.visit_path('/')

      expect(browser).to have_body 'teststring'
    end
  end

  context 'deploying a PHP7 app with custom conf files in php.ini.d dir in app root' do
    let(:app_name) { 'php_7_with_php_ini_d' }

    it 'sets custom configurations' do
      expect(app).to be_running
      browser.visit_path('/')

      expect(browser).to have_body 'teststring'
    end
  end

  context 'deploying a PHP71 app with custom conf files in php.ini.d dir in app root' do
    let(:app_name) { 'php_71_with_php_ini_d' }

    it 'sets custom configurations' do
      expect(app).to be_running
      browser.visit_path('/')

      expect(browser).to have_body 'teststring'
    end
  end

  context 'deploying an app with an invalid extension in php.ini.d dir' do
    let(:app_name) { 'invalid_php_ini_d' }

    it 'fails during staging' do
      expect(app).to have_logged "The extension 'meatball' is not provided by this buildpack."
    end
  end
end

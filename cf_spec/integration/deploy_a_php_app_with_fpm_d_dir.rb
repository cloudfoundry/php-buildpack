$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) do
    Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}})
  end
  let(:browser)  { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic PHP5 app with custom conf files in fpm.d dir in app root' do
    let(:app_name) { 'php_5_with_fpm_d' }

    it 'expects an app to be running' do
      expect(app).to be_running
    end

    it 'sets custom configurations' do
      browser.visit_path('/index.php')
      expect(browser).to have_body 'TEST_HOME_PATH'
      expect(browser).to have_body '/home/vcap/app/test/path'
      expect(browser).to have_body 'TEST_WEBDIR'
      expect(browser).to have_body 'htdocs'
    end
  end

  context 'deploying a PHP7 app with custom conf files in fpm.d dir in app root' do
    let(:app_name) { 'php_7_with_fpm_d' }

    it 'expects an app to be running' do
      expect(app).to be_running
    end

    it 'sets custom configurations' do
      browser.visit_path('/index.php')
      expect(browser).to have_body 'TEST_HOME_PATH'
      expect(browser).to have_body '/home/vcap/app/test/path'
      expect(browser).to have_body 'TEST_WEBDIR'
      expect(browser).to have_body 'htdocs'
    end
  end

  context 'deploying a PHP71 app with custom conf files in fpm.d dir in app root' do
    let(:app_name) { 'php_71_with_fpm_d' }

    it 'expects an app to be running' do
      expect(app).to be_running
    end

    it 'sets custom configurations' do
      browser.visit_path('/index.php')
      expect(browser).to have_body 'TEST_HOME_PATH'
      expect(browser).to have_body '/home/vcap/app/test/path'
      expect(browser).to have_body 'TEST_WEBDIR'
      expect(browser).to have_body 'htdocs'
    end
  end
end


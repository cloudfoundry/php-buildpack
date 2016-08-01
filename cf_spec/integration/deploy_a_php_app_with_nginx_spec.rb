$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do

  let(:browser) { Machete::Browser.new(@app) }
  before(:each) do
    @app = Machete.deploy_app(
      'php_app_using_nginx',
      env_config
    )
  end
  after(:each) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using Nginx as the webserver' do
    let (:env_config) { {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}} }

    it 'compiles and starts the app' do
      expect(@app).to be_running
    end

    it 'shows the current buildpack version for useful info' do
      expect(@app).to have_logged "-------> Buildpack version #{File.read(File.expand_path('../../../VERSION', __FILE__)).chomp}"
    end

    it 'installs nginx, the request web server' do
      expect(@app).to have_logged 'Installing Nginx'
    end

    it 'the root endpoint renders a dynamic message' do
      browser.visit_path('/')
      expect(browser).to have_body('PHP Version')
    end

    context 'in offline mode', :cached do
      let (:env_config) { {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}} }

      specify do
        expect(@app).not_to have_internet_traffic
      end
    end

    context 'using default versions' do
      let (:env_config)  do
       { env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'], 'BP_DEBUG' => 1} }
      end

      it 'installs the default version of nginx' do
       expect(@app).to have_logged 'DEBUG: default_version_for nginx is'
      end
    end
  end
end


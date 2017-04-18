$: << 'cf_spec'
require 'cf_spec_helper'
require 'excon'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'with_httpd'}

  context 'deploying a basic PHP app using httpd as the webserver' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'compiles and starts the app' do
      expect(@app).to be_running
    end

    it 'shows the current buildpack version for useful info' do
      expect(@app).to have_logged "-------> Buildpack version #{File.read(File.expand_path('../../../VERSION', __FILE__)).chomp}"
    end

    it 'installs httpd, the request web server' do
      expect(@app).to have_logged 'Installing HTTPD'
    end

    it 'logs the httpd version' do
      buildpack_root = File.join(File.dirname(__FILE__), '..', '..')
      default_version_script = File.join(buildpack_root, 'compile-extensions', 'bin', 'default_version_for')
      manifest_path = File.join(buildpack_root, 'manifest.yml')
      httpd_version = `#{default_version_script} #{manifest_path} httpd`.strip

      expect(@app).to have_logged "HTTPD #{httpd_version}"
    end

    it 'the root endpoint renders a dynamic message' do
      browser.visit_path('/')
      expect(browser).to have_body('PHP Version')
    end

    it 'compresses dynamic content' do
      response = Excon.get("http://#{browser.base_url}/index.php", :headers => {'Accept-Encoding' => 'gzip'})
      expect(response.status).to eq(200)
      expect(response.headers['Server']).to eq('Apache')
      expect(response.headers['Content-Encoding']).to eq('gzip')
    end

    it 'compresses static content' do
      response = Excon.get("http://#{browser.base_url}/staticfile.html", :headers => {'Accept-Encoding' => 'gzip'})
      expect(response.status).to eq(200)
      expect(response.headers['Server']).to eq('Apache')
      expect(response.headers['Content-Encoding']).to eq('gzip')
    end
  end

  context 'in offline mode', :cached do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    specify do
      expect(@app).not_to have_internet_traffic
    end
  end

  context 'using default versions' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'], 'BP_DEBUG' => 1}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'installs the default version of httpd' do
      expect(@app).to have_logged '"update_default_version" is setting [HTTPD_VERSION]'
    end
  end
end


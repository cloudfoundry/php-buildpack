$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'php_app_using_httpd'}

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

    it 'the root endpoint renders a dynamic message' do
      browser.visit_path('/')
      expect(browser).to have_body('PHP Version')
    end

    it 'compresses dynamic content' do
      headers = getHeaders('/index.php', ['Accept-Encoding: gzip'])

      expect(headers).to include('Server: Apache')
      expect(headers).to include('Content-Encoding: gzip')
    end

    it 'compresses static content' do
      headers = getHeaders('/staticfile.html', ['Accept-Encoding: gzip'])

      expect(headers).to include('Server: Apache')
      expect(headers).to include('Content-Encoding: gzip')
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

  require 'socket'
  def getHeaders(path, headers = [])
    host = browser.base_url
    Socket.tcp(host, 80) do |sock|
      sock.print "GET #{path} HTTP/1.0\r\nHost: #{host}\r\n"
      headers.each do |header|
        sock.print header
        sock.print "\r\n"
      end
      sock.print "\r\n"
      sock.close_write
      sock.read.split(/\n\r?\n/, 2).first.split(/\r?\n/)
    end
  end
end


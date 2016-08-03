$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'php_app'}

  context 'deploying a basic PHP app' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'displays the buildpack version' do
      expect(@app).to have_logged "-------> Buildpack version #{File.read(File.expand_path('../../../VERSION', __FILE__)).chomp}"
    end

    it 'installs a current version of PHP' do
      expect(@app).to have_logged 'Installing PHP'
      expect(@app).to have_logged 'PHP 5.5'
    end

    it 'does not return the version of PHP in the response headers' do
      browser.visit_path('/')
      expect(browser).to have_body 'PHP Version'
      expect(browser).not_to have_header 'X-Powered-By'
    end

    it 'does not display a warning message about the php version config' do
        expect(@app).to_not have_logged 'WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.'
        expect(@app).to_not have_logged 'WARNING: The version defined in `composer.json` will be used.'
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

    it 'does not call out to the internet' do
      expect(@app).not_to have_internet_traffic
    end

    it 'downloads the binaries directly from the buildpack' do
      expect(@app).to have_logged %r{Downloaded \[file://.*/dependencies/https___buildpacks.cloudfoundry.org_concourse-binaries_php_php-5.5.\d+-linux-x64-\d+.tgz\] to \[/tmp\]}
    end
  end

  context 'using default versions' do
    before(:all) do
      @env_config = {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'], 'BP_DEBUG' => 1}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'installs the default version of PHP' do
      expect(@app).to have_logged '"update_default_version" is setting [PHP_VERSION]'
    end

    it 'installs the default version of composer' do
      expect(@app).to have_logged 'DEBUG: default_version_for composer is'
    end

  end
end


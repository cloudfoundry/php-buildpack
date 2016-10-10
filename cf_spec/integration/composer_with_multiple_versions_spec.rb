$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }

  context 'PHP version is specified in both' do
    before(:all) do
      @env_config = {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app_name = 'composer_with_multiple_versions'
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'installs the version of PHP defined in `composer.json`' do
      expect(@app).to have_logged 'Installing PHP'
      expect(@app).to have_logged 'PHP 5.6'
    end

    it 'does not install the PHP version defined in `options.json`' do
      expect(@app).to_not have_logged 'PHP 5.5'
    end

    it 'displays a useful warning message that `composer.json` is being used over `options.json`' do
      expect(@app).to have_logged 'WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.'
      expect(@app).to have_logged 'WARNING: The version defined in `composer.json` will be used.'
    end
  end

  context 'PHP version is specified in neither' do
    before(:all) do
      @env_config = {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'], 'BP_DEBUG' => 1}}
      # this app has a composer.json and a .bp-config/options.json, neither of which
      # specifiy a PHP version. So we use it for this test
      @app_name = 'php_5_app_with_all_modules_using_composer'
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'installs the default version of PHP' do
      expect(@app).to have_logged '"update_default_version" is setting [PHP_VERSION]'
    end

    it 'doesn\'t display a warning message' do
      expect(@app).to_not have_logged 'WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.'
      expect(@app).to_not have_logged 'WARNING: The version defined in `composer.json` will be used.'
    end
  end

  context 'PHP version is specified in composer.json but not options.json' do
    before(:all) do
      @env_config = {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      # this app has a composer.json and a .bp-config/options.json. Only the composer.json
      # specifies a PHP version. So we use it for this test
      @app_name = 'php_7_app_with_all_modules_using_composer'
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'installs the version of PHP defined in `composer.json`' do
      expect(@app).to have_logged 'Installing PHP'
      expect(@app).to have_logged 'PHP 7.0'
    end

    it 'doesn\'t display a warning message' do
      expect(@app).to_not have_logged 'WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.'
      expect(@app).to_not have_logged 'WARNING: The version defined in `composer.json` will be used.'
    end
  end
end


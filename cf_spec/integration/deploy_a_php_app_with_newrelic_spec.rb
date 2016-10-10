$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  context 'in offline mode', :cached do
    let(:browser)  { Machete::Browser.new(@app) }

    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'], 'BP_DEBUG' => 'true' }}
      @app_name = 'php_app_with_newrelic'
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'does not call out to the internet' do
      expect(@app).not_to have_internet_traffic
    end

    it 'downloads the binaries directly from the buildpack' do
      expect(@app).to have_logged %r{Downloaded \[file://.*/dependencies/https___download.newrelic.com_php_agent_archive_[\d\.]+_newrelic-php5-[\d\.]+-linux\.tar\.gz\] to \[/tmp\]}
    end

    it 'sets up New Relic' do
      expect(@app).to have_logged('Installing NewRelic')
      expect(@app).to have_logged('NewRelic Installed')
    end

    it 'installs the default version of newrelic' do
     expect(@app).to have_logged 'Using NewRelic default version:'
    end
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser)  { Machete::Browser.new(@app) }

  before(:context) { @app_name = 'php_geoip_app'}

  context 'deploying a basic PHP app' do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app(@app_name, @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'is able to use the geoip databases' do
      expect(@app).to be_running
      browser.visit_path("/")
      expect(browser).to have_body /Avail: 1/
      expect(browser).to have_body /Info: GEO-106FREE/
      expect(browser).to have_body /Country: US/
    end

    it 'has downloaded geoip dbs' do
        expect(@app).to have_logged 'Downloading Geoip Databases.'
        expect(@app).to have_logged 'file_name: GeoLiteCityv6.dat'
        expect(@app).to have_logged 'file_name: GeoIPv6.dat'
        expect(@app).to have_logged 'file_name: GeoLiteCountry.dat'
        expect(@app).to have_logged 'file_name: GeoLiteASNum.dat'
        expect(@app).to have_logged 'file_name: GeoLiteCity.dat'
    end
  end

  context 'in offline mode', :cached do
    before(:all) do
      @env_config = {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
      @app = deploy_app("php_geoip_app_local_deps", @env_config)
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'does not call out to the internet' do
      expect(@app).not_to have_internet_traffic
    end

    it 'downloads the binaries directly from the buildpack' do
      expect(@app).to have_logged "Copying Geoip Databases from App."
    end
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }

  context 'deploying a symfony app with locally-vendored dependencies', :cached do
    before(:context) do
      @app = Machete.deploy_app('symfony_hello_world_with_local_dependencies', {})
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'that root route has content that is dynamically generated' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end

    it 'installs PHP 5.4 with composer and shows the deprecation message' do
      expect(@app).to have_logged 'PHP 5.4'
      expect(@app).to have_logged 'DEPRECATION WARNING: PHP 5.4 is being declared "End of Life" as of 2015-09-14'
      expect(@app).to have_logged 'DEPRECATION WARNING: See https://secure.php.net/supported-versions.php for more details'
      expect(@app).to have_logged 'DEPRECATION WARNING: Upgrade guide can be found at https://secure.php.net/manual/en/migration55.php'
      expect(@app).to have_logged 'DEPRECATION WARNING: The php-buildpack will no longer support PHP 5.4 after this date'
    end

    it 'supports Symphony app routing' do
      browser.visit_path('/hello/foo')
      expect(browser).to have_body "Hello foo!\n\nRunning on Symfony!"
    end

    it 'does not call out to the internet during staging' do
      expect(@app.host).not_to have_internet_traffic
    end
  end

  context 'deploying a symfony app with remotely-sourced dependencies', :uncached do
    before(:context) do
      @app = Machete.deploy_app('symfony_hello_world_with_remote_dependencies', {
        env: {
          'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']
        }
      })
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'that root route has content that is dynamically generated' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end
  end
end



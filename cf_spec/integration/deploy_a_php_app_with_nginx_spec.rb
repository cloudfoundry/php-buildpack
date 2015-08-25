$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do

  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'php_app_using_nginx',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end
  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using Nginx as the webserver' do
    it 'compiles and starts the app' do
      expect(@app).to be_running
    end

    it 'shows the current buildpack version for useful info' do
      expect(@app).to have_logged "-------> Buildpack version #{File.read(File.expand_path('../../../VERSION', __FILE__)).chomp}"
    end

    it 'installs nginx, the request web server' do
      expect(@app).to have_logged 'Installing Nginx'
    end

    it 'installs PHP 5.4 specified with options.json and shows the deprecation message' do
      expect(@app).to have_logged 'PHP 5.4'
      expect(@app).to have_logged 'DEPRECATION WARNING: PHP 5.4 is being declared "End of Life" as of 2015-09-14'
      expect(@app).to have_logged 'DEPRECATION WARNING: See https://secure.php.net/supported-versions.php for more details'
      expect(@app).to have_logged 'DEPRECATION WARNING: Upgrade guide can be found at https://secure.php.net/manual/en/migration55.php'
      expect(@app).to have_logged 'DEPRECATION WARNING: The php-buildpack will no longer support PHP 5.4 after this date'
    end

    it 'the root endpoint renders a dynamic message' do
      browser.visit_path('/')
      expect(browser).to have_body('PHP Version')
    end

    context 'in offline mode', :cached do
      specify do
        expect(@app.host).not_to have_internet_traffic
      end
    end
  end
end


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

    specify do
      expect(@app).to be_running

      expect(@app).to have_logged "-------> Buildpack version #{File.read(File.expand_path('../../../VERSION', __FILE__)).chomp}"
      expect(@app).to have_logged 'Installing Nginx'
      expect(@app).to have_logged 'Installing PHP'
      expect(@app).to have_logged 'PHP 5.5'

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


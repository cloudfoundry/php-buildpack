$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do

  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'php_app_using_invalid_webserver',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end
  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context "deploying a basic PHP app using 'apache' as the webserver" do
    it 'compiles and starts the app' do
      expect(@app).not_to be_running
    end

    it 'shows an error message indicating the supported web servers' do
      expect(@app).to have_logged "apache isn't a supported web server. Supported web servers are 'httpd' & 'nginx'"
    end
  end
end


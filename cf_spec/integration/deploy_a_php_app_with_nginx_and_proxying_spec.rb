$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'php_app_using_nginx_and_proxying',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end
  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using Nginx as the webserver' do
    it 'does not set the HTTP_PROXY environment variable as the Proxy header value' do
      app_url = Machete::CF::CLI.url_for_app(@app)
      response_output = `curl -H "Proxy: http://example.com" #{app_url}`
      expect(response_output).to eq("HTTP_PROXY env var is: ")
      expect(response_output).to_not include("example.com")
    end
  end
end


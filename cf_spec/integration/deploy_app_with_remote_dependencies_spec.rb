$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'the application has remote dependencies', :uncached do
    let(:app_name) { 'app_with_remote_dependencies' }

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'App with remote dependencies running'
    end
  end
end


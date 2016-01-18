$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, options) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a Zend app with locally-vendored dependencies', :cached do
    let(:app_name) { 'zend_framework_hello_world_with_local_dependencies' }
    let(:options) do
      {}
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Zend Framework 2'

      expect(app).not_to have_internet_traffic
    end
  end

  context 'deploying a Zend app with remote dependencies', :uncached do
    let(:app_name) { 'zend_framework_hello_world_with_remote_dependencies' }
    let(:options) do
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Zend Framework 2'
    end
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, options) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a symfony app with locally-vendored dependencies', if: Machete::BuildpackMode.cached? do
    let(:app_name) { 'symfony_hello_world_with_local_dependencies' }
    let(:options) do
      {}
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'

      browser.visit_path('/hello/foo')
       expect(browser).to have_body "Hello foo!\n\nRunning on Symfony!"

      expect(app.host).not_to have_internet_traffic
    end
  end

  context 'deploying a symfony app with remotely-sourced dependencies', if: Machete::BuildpackMode.uncached? do
    let(:app_name) { 'symfony_hello_world_with_remote_dependencies' }
    let(:options) do
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end
  end

end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, options) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a Cake application with local dependencies', if: Machete::BuildpackMode.offline? do
    let(:app_name) { 'cake_with_local_dependencies' }
    let(:options) do
      {
        with_pg: true
      }
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'CakePHP'
      expect(browser).not_to have_body 'Missing Database Table'

      expect(app.host).not_to have_internet_traffic
    end

    specify 'visiting a non-root path' do
      browser.visit_path('/users/add')

      expect(browser).to have_body('Add New User')
    end
  end

  context 'deploying a Cake application with remote dependencies', if: Machete::BuildpackMode.online? do
    let(:app_name) { 'cake_with_remote_dependencies' }
    let(:options) do
      {
        with_pg: true,
        env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}
      }
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'CakePHP'
      expect(browser).not_to have_body 'Missing Database Table'
    end
  end
end


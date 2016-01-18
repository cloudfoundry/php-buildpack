$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name, options) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a Cake application with local dependencies', :cached do
    let(:app_name) { 'cake_with_local_dependencies' }
    let(:options) do
      {
        start_command: "$HOME/app/Console/cake schema create -y && $HOME/.bp/bin/start"
      }
    end

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'CakePHP'
      expect(browser).not_to have_body 'Missing Database Table'

      browser.visit_path('/users/add')
      expect(browser).to have_body('Add New User')

      expect(app).not_to have_internet_traffic
    end
  end

  context 'deploying a Cake application with remote dependencies', :uncached do
    let(:app_name) { 'cake_with_remote_dependencies' }
    let(:options) do
      {
        env: {
          'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN'],
        },
        start_command: "$HOME/app/Console/cake schema create -y && $HOME/.bp/bin/start"
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


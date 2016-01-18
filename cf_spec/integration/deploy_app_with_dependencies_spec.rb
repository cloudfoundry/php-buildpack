$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_local_dependencies',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end
  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'the application has vendored dependencies' do

    specify do
      expect(@app).to be_running

      browser.visit_path('/')
      expect(browser).to have_body 'App with dependencies running'
    end

    context 'in offline mode', :cached do
      specify do
        expect(@app).not_to have_internet_traffic
      end
    end

  end
end



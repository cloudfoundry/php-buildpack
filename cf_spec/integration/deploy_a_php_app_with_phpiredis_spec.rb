$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_phpiredis',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using phpiredis module' do
    context 'after the phpiredis module has been loaded into PHP' do
      it 'expects CF to report the app is running' do
        expect(@app).to be_running
      end

      it 'logs that the approrpiate phpiredis method was invoked' do
        browser.visit_path('/')
        expect(@app).to have_logged "PHP message: PHP Warning:  phpiredis_command_bs() expects parameter 1 to be resource"
      end
    end
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_amqp',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using AMQP module' do
    context 'after the AMQP module has been loaded into PHP' do
      it 'expects CF to report the app is running' do
        expect(@app).to be_running
      end

      it 'logs that AMQP could not connect to a server' do
        expect { browser.visit_path('/') }.to raise_error(Machete::HTTPServerError)
        expect(@app).to have_logged "PHP message: PHP Fatal error:  Uncaught exception 'AMQPConnectionException'"
      end
    end
  end
end

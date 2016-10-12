$: << 'cf_spec'
require 'cf_spec_helper'

describe 'App that uses Kafka' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_rdkafka',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using RdKafka module' do
    context 'after the RdKafka module has been loaded into PHP' do
      it 'expects CF to report the app is running' do
        expect(@app).to be_running
      end

      it 'logs that Producer could not connect to a Kafka server' do
        browser.visit_path('/producer.php')
        expect(browser).to have_body /Kafka error: Local: Broker transport failure/
      end
    end
  end
end

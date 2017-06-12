$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app_name = 'with_cassandra'
    @app = Machete.deploy_app(
      @app_name,
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )

    @service_name = "cassandra-test-service-php-#{Random.rand(100000)}"
    Machete::SystemHelper.run_cmd(%(cf cups #{@service_name} -p '{"username":"uname","password":"pwd","node_ips":["1.1.1.1","2.2.2.2"]}'))
    Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@service_name}))
    Machete::SystemHelper.run_cmd(%(cf unbind-service #{@app_name} #{@app_name}-test-service))
    Machete::SystemHelper.run_cmd(%(cf restage #{@app_name}))
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
    Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@service_name}))
  end

  context 'deploying a basic PHP app using Cassandra module' do
    context 'after the Cassandra module has been loaded into PHP' do
      it 'expects CF to report the app is running' do
        expect(@app).to be_running
      end

      it 'logs that Cassandra could not connect to a server' do
        expect { browser.visit_path('/') }.to raise_error(Machete::HTTPServerError)
        expect(@app).to have_logged 'No hosts available for the control connection'
        expect(@app).to have_logged 'Cassandra\\\\DefaultCluster->connect()'
      end
    end
  end
end

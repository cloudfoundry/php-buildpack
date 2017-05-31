$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid"}'))
      Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@dynatrace_service_name}))
      Machete::SystemHelper.run_cmd(%(cf restage #{@app_name}))
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
      Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@dynatrace_service_name}))
    end

    it 'initializing dynatrace agent' do
     expect(@app).to have_logged 'Initializing'
    end

    it 'downloading dynatrace agent' do
     expect(@app).to have_logged 'Downloading Dynatrace PAAS-Agent Installer'
    end

    it 'extracting dynatrace agent' do
     expect(@app).to have_logged 'Extracting Dynatrace PAAS-Agent'
    end

    it 'removing dynatrace agent installer' do
     expect(@app).to have_logged 'Removing Dynatrace PAAS-Agent Installer'
    end

    it 'adding environment vars' do
     expect(@app).to have_logged 'Adding Dynatrace specific Environment Vars'
    end

    it 'LD_PRELOAD settings' do
     expect(@app).to have_logged 'Adding Dynatrace LD_PRELOAD settings'
    end
  end
end

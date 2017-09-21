$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  context '' do
    let(:browser)  { Machete::Browser.new(@app) }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_appdynamics'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "appdynamics-test-service-php"

      Machete::SystemHelper.run_cmd(%(cf cups #{@appdynamics_service_name} -p '{"account-access-key":"fe244dc3-372f-4d36-83b0-379973103c5d","account-name":"customer1","host-name":"testhostname.com","port":"8090","ssl-enabled":"False"}'))
      Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@appdynamics_service_name}))
      Machete::SystemHelper.run_cmd(%(cf restage #{@app_name}))
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
      Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@appdynamics_service_name}))
    end

    it 'should compile appdynamics agent' do
      expect(@app).to have_logged 'AppDynamics service detected, beginning compilation'
    end

    it 'should configure appdynamics agent' do
      expect(@app).to have_logged 'Running AppDynamics extension method _configure'
    end

    it 'should set credentials for appdynamics agent' do
      expect(@app).to have_logged 'Setting AppDynamics credentials info...'
    end

    it 'should download appdynamics agent' do
      expect(@app).to have_logged 'Downloading AppDynamics package...'
    end

    it 'should install appdynamics agent' do
      expect(@app).to have_logged 'Installing AppDynamics package...'
    end

  end
end

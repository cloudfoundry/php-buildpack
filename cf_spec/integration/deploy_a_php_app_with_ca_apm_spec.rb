$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  context '' do
    let(:browser)  { Machete::Browser.new(@app) }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_ca_apm'
      @app = deploy_app(@app_name, @env_config)
      @caapm_service_name = "caapm-test-php-service-#{Random.rand(1000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@caapm_service_name} -p '{"collport":"9009","collhost":"abcd.ca.com","appname":"my-integration-test"}'))
      Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@caapm_service_name}))
      Machete::SystemHelper.run_cmd(%(cf restage #{@app_name}))
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
      Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@caapm_service_name}))
    end

    
    it 'load service info check' do
      expect(@app).to have_logged 'Loading service info to find CA APM Service'
      expect(@app).to have_logged 'Using the first CA APM service present in user-provided services'
      expect(@app).to have_logged 'IA Agent Host [abcd.ca.com]'
      expect(@app).to have_logged 'IA Agent Port [9009]'
      expect(@app).to have_logged 'PHP App Name [my-integration-test]'
    end


    it 'downloading CA APM binaries' do
      expect(@app).to have_logged 'Downloading CA APM PHP Agent package...'      
      expect(@app).to have_logged 'Downloaded CA APM PHP Agent package'
    end

    
    it 'Running CA APM installer script' do
      expect(@app).to have_logged('Compiling CA APM PHP Agent install commands')      
      expect(@app).to have_logged('Installing CA APM PHP Agent')
      expect(@app).to have_logged('Installing CA PHP Probe Agent...')      
      expect(@app).to have_logged('Installation Status : Success')       
    end

    it 'modifying php ini' do
      expect(@app).to have_logged('Updating PHP INI file with CA APM PHP Agent Properties')     
    end  

    it 'installation complete' do
      expect(@app).to have_logged('CA APM PHP Agent installation completed')     
    end   
    
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Deploy app with single dynatrace service without manifest.json' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid"}'))
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

    it 'detecting single dynatrace service' do
     expect(@app).to have_logged 'Found one matching Dynatrace service'
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

    it 'checking for manifest.json fallback' do
     expect(@app).to have_logged 'Agent path not found in manifest.json, using fallback'
    end
  end
end

describe 'Deploy app with single dynatrace service and manifest.json' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas/manifest","environmentid":"envid"}'))
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

    it 'detecting single dynatrace service' do
     expect(@app).to have_logged 'Found one matching Dynatrace service'
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

    it 'using manifest.json' do
     expect(@app).to have_logged 'Using manifest.json'
    end
  end
end

describe 'Deploy app with multiple dynatrace services' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"
      @dynatrace_service_name_dupe = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid"}'))
      Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@dynatrace_service_name}))

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name_dupe} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid_dupe"}'))
      Machete::SystemHelper.run_cmd(%(cf bind-service #{@app_name} #{@dynatrace_service_name_dupe}))

      Machete::SystemHelper.run_cmd(%(cf restage #{@app_name}))
    end

    after(:all) do
      Machete::CF::DeleteApp.new.execute(@app)
      Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@dynatrace_service_name}))
      Machete::SystemHelper.run_cmd(%(cf delete-service -f #{@dynatrace_service_name_dupe}))
    end

    it 'initializing dynatrace agent' do
     expect(@app).to have_logged 'Initializing'
    end

    it 'detecting multiple dynatrace services' do
     expect(@app).to have_logged 'More than one matching service found!'
    end

    it 'deployment should fail' do
     expect(@app).to_not be_running
    end
  end
end

describe 'Deploy app with single dynatrace service, wrong url and skiperrors on true' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paasFAIL","environmentid":"envid","skiperrors":"true"}'))
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

    it 'detecting single dynatrace service' do
     expect(@app).to have_logged 'Found one matching Dynatrace service'
    end

    it 'downloading dynatrace agent' do
     expect(@app).to have_logged 'Downloading Dynatrace PAAS-Agent Installer'
    end

    it 'download retries work' do
     expect(@app).to have_logged 'Error during installer download, retrying in 4 seconds'
     expect(@app).to have_logged 'Error during installer download, retrying in 5 seconds'
     expect(@app).to have_logged 'Error during installer download, retrying in 7 seconds'
    end

    it 'should exit gracefully' do
     expect(@app).to have_logged 'Error during installer download, skipping installation'
    end

    it 'no further installer logs' do
     expect(@app).to_not have_logged 'Extracting Dynatrace PAAS-Agent'
    end

    it 'deployment should not fail' do
     expect(@app).to be_running
    end
  end
end

describe 'Deploy app with single dynatrace service, wrong url and skiperrors not set' do
  context '' do
    let(:browser) {
      Machete::Browser.new(@app)
    }

    before(:all) do
      @env_config = {env: {'BP_DEBUG' => 'true' }}
      @app_name = 'with_dynatrace'
      @app = deploy_app(@app_name, @env_config)
      @dynatrace_service_name = "dynatrace-test-service-php-#{Random.rand(100000)}"

      Machete::SystemHelper.run_cmd(%(cf cups #{@dynatrace_service_name} -p '{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paasFAIL","environmentid":"envid"}'))
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

    it 'detecting single dynatrace service' do
     expect(@app).to have_logged 'Found one matching Dynatrace service'
    end

    it 'downloading dynatrace agent' do
     expect(@app).to have_logged 'Downloading Dynatrace PAAS-Agent Installer'
    end

    it 'download retries work' do
     expect(@app).to have_logged 'Error during installer download, retrying in 4 seconds'
     expect(@app).to have_logged 'Error during installer download, retrying in 5 seconds'
     expect(@app).to have_logged 'Error during installer download, retrying in 7 seconds'
    end

    it 'error during agent download' do
     expect(@app).to have_logged 'ERROR: Dynatrace agent download failed'
    end

    it 'no further installer logs' do
     expect(@app).to_not have_logged 'Extracting Dynatrace PAAS-Agent'
    end

    it 'deployment should fail' do
     expect(@app).to_not be_running
    end
  end
end


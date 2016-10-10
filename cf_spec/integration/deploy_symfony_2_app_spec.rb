$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }

  context 'deploying a symfony 2.1 app with locally-vendored dependencies', :cached do
    before(:context) do
      @app = Machete.deploy_app('symfony_2_hello_world_with_local_dependencies', {})
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'dynamically generates the content for the root route' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end

    it 'supports Symphony app routing' do
      browser.visit_path('/hello/foo')
      expect(browser).to have_body "Hello foo!\n\nRunning on Symfony!"
    end

    # it 'does not call out to the internet during staging' do
    #   expect(@app).not_to have_internet_traffic
    # end
  end

  context 'deploying a symfony 2.1 app with remotely-sourced dependencies', :uncached do
    before(:context) do
      @app = Machete.deploy_app('symfony_2_hello_world_with_remote_dependencies', {
        env: {
          'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']
        }
      })
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'dynamically generates the content for the root route' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end
  end

  context 'deploying a symfony 2.8 app with locally-vendored dependencies', :cached do
    before(:context) do
      @app = Machete.deploy_app('symfony_2.8_with_remote_dependencies', {})
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'that root route has content that is dynamically generated' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end

    # it 'does not call out to the internet during staging' do
    #   expect(@app).not_to have_internet_traffic
    # end
  end

  context 'deploying a symfony 2.8 app with remotely-sourced dependencies', :uncached do
    before(:context) do
      @app = Machete.deploy_app('symfony_2.8_with_remote_dependencies', {
        env: {
          'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']
        }
      })
    end

    after(:context) do
      Machete::CF::DeleteApp.new.execute(@app)
    end

    it 'expects an app to be running' do
      expect(@app).to be_running
    end

    it 'that root route has content that is dynamically generated' do
      browser.visit_path("/")
      expect(browser).to have_body 'Running on Symfony!'
    end
  end
end

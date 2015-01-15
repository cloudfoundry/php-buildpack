$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    # Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a Zend app with locally-vendored dependencies', if: Machete::BuildpackMode.offline? do
    let(:app_name) { 'zend_framework_hello_world_with_local_dependencies' }

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Zend Framework 2'

      expect(app.host).not_to have_internet_traffic
    end
  end

  context 'deploying a Zend app with remote dependencies', if: Machete::BuildpackMode.online? do
    let(:app_name) { 'zend_framework_hello_world_with_remote_dependencies' }

    specify do
      expect(app).to be_running

      browser.visit_path("/")
      expect(browser).to have_body 'Zend Framework 2'
    end
  end
end

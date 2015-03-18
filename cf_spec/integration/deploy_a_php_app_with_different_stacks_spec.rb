$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack with with different stacks' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a basic PHP app on a lucid64 rootfs', if: ENV['CF_STACK'] == 'lucid64' do
    let(:app_name) { 'php_app' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged 'lucid'
      expect(app).to_not have_logged 'trusty'
    end
  end

  context 'deploying a basic PHP app on a cflinuxfs2 rootfs', if: ENV['CF_STACK'] == 'cflinuxfs2' do
    let(:app_name) { 'php_app' }

    specify do
      expect(app).to be_running

      expect(app).to_not have_logged 'lucid'
      expect(app).to have_logged 'trusty'
    end
  end
end

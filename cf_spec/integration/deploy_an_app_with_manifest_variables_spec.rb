$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying a composer app with post install commands' do
    let(:app_name) { 'composer_environment_sniffer' }

    specify do
      expect(app).to have_logged "MANIFEST_VARIABLE: 'VARIABLE_IS_SET'"
      expect(app).to have_logged 'PHP said MANIFEST_VARIABLE: VARIABLE_IS_SET'
    end
  end
end


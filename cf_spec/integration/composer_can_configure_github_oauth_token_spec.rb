$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Composer' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => oauth_token}}) }
  let(:app_name) { 'app_with_local_dependencies' }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying an app with valid $COMPOSER_GITHUB_OAUTH_TOKEN variable set', :uncached do
    let(:oauth_token) { ENV['COMPOSER_GITHUB_OAUTH_TOKEN'] }
    specify do
      expect(app).to be_running

      expect(app).to have_logged "-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN"
    end
  end

  context 'deploying an app with an invalid $COMPOSER_GITHUB_OAUTH_TOKEN', :uncached do
    let(:oauth_token) { 'badtoken123123' }

    specify do
      expect(app).to have_logged "-----> The GitHub OAuth token supplied from $COMPOSER_GITHUB_OAUTH_TOKEN is invalid"
    end
  end
end


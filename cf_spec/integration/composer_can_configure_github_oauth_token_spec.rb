$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Composer' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying an app with $COMPOSER_GITHUB_OAUTH_TOKEN variable set', if: Machete::BuildpackMode.online? do
    let(:app_name) { 'app_with_local_dependencies' }

    specify do
      expect(app).to be_running

      expect(app).to have_logged "-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN"
    end
  end
end


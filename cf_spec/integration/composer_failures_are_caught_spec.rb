$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Composer failures' do
  subject(:app) { Machete.deploy_app(app_name, {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'deploying an app with an impossible dependency in composer.json', :uncached do
    let(:app_name) { 'composer_with_impossible_dependency' }

    specify do
      expect(app).to_not be_running

      expect(app).to have_logged '-----> Composer command failed'
    end
  end
end


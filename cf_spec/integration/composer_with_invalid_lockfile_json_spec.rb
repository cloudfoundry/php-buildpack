$: << 'cf_spec'
require 'cf_spec_helper'

describe "When composer.lock is invalid JSON" do
  let(:app_name) { 'composer_with_invalid_lockfile_json' }

  subject(:app) do
    Machete.deploy_app(app_name, {env:
      {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}
    })
  end

  after do
    #Machete::CF::DeleteApp.new.execute(app)
  end

  context 'with an uncached buildpack', :uncached do
    specify do
      expect(app).to_not be_running
      expect(app).to have_logged("Invalid JSON present in composer.lock. Parser said")
    end
  end

  context 'with a cached buildpack', :cached do
    specify do
      expect(app).to_not be_running
      expect(app).to have_logged('Invalid JSON present in composer.lock. Parser said')
    end
  end
end



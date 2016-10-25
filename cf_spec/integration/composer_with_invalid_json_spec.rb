$: << 'cf_spec'
require 'cf_spec_helper'

describe "When composer.json is invalid JSON" do
  subject(:app) do
    Machete.deploy_app(app_name, {env:
      {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}
    })
  end
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'with an uncached buildpack', :uncached do
    let(:app_name) { 'composer_with_invalid_json' }

    specify do
      expect(app).to_not be_running
      expect(app).to have_logged("Invalid JSON present in composer.json. Parser said")
    end
  end

  context 'with a cached buildpack', :cached do
    let(:app_name) { 'composer_with_invalid_json' }

    specify do
      expect(app).to_not be_running
      expect(app).to have_logged('Invalid JSON present in composer.json. Parser said')
    end
  end
end



$: << 'cf_spec'
require 'cf_spec_helper'

describe "Composer with version set to 'latest'" do
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
    let(:app_name) { 'composer_with_version_set_to_latest' }

    specify do
      expect(app).to be_running
      expect(app).to have_logged("Downloaded [https://getcomposer.org/composer.phar] to [/tmp/composer.phar]")
    end
  end

  context 'with a cached buildpack', :cached do
    let(:app_name) { 'composer_with_version_set_to_latest' }

    specify do
      expect(app).to_not be_running
      expect(app).to have_logged('"COMPOSER_VERSION": "latest" is not supported in the cached buildpack. Please vendor your preferred version of composer with your app, or use the provided default composer version.')
    end
  end
end


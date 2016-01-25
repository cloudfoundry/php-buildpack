$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'composer_with_multiple_versions',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  it 'expects an app to be running' do
    expect(@app).to be_running
  end

  it 'installs the version of PHP defined in `composer.json`' do
    expect(@app).to have_logged 'Installing PHP'
    expect(@app).to have_logged 'PHP 5.5'
  end

  it 'does not install the PHP version defined in `options.json`' do
    expect(@app).to_not have_logged 'PHP 5.6'
  end

  it 'displays a useful warning message that `composer.json` is being used over `options.json`' do
    expect(@app).to have_logged 'WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.'
    expect(@app).to have_logged 'WARNING: The version defined in `composer.json` will be used.'
  end
end


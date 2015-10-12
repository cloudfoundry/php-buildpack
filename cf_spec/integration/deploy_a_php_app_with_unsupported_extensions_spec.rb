$: << 'cf_spec'
require 'cf_spec_helper'

describe 'An app deployed specifying unsupported extensions' do

  before(:all) do
    @app     = Machete.deploy_app 'php_app_with_unsupported_extensions'
    @browser = Machete::Browser.new(@app)
  end

  it 'should be running' do
    expect(@app).to be_running
  end

  it 'should say which extensions are not supported' do
    expect(@app).to have_logged 'The extension \'meatball\' is not provided by this buildpack.'
    expect(@app).to have_logged 'The extension \'hotdog\' is not provided by this buildpack.'
  end

  it 'should not display default php startup warning messages' do
    expect(@app).not_to have_logged /PHP message: PHP Warning:  PHP Startup: Unable to load dynamic library/
  end

  context 'and valid extensions' do
    it 'should say which extensions are not supported' do
      expect(@app).not_to have_logged 'The extension \'curl\' is not provided by this buildpack.'
    end

    it 'should load the module without issue' do
      @browser.visit_path('/')
      expect(@browser).to have_body('curl module has been loaded successfully')
    end

  end

  after(:all) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

end


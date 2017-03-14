$: << 'cf_spec'
require 'cf_spec_helper'

describe 'deploying a basic PHP app with compiled modules in PHP_EXTENSIONS' do
  before(:context) do
    @app = Machete.deploy_app(
      'with_compiled_modules'
    )
    @browser = Machete::Browser.new(@app)
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'when the app is pushed' do
    it 'does not log an error metioning libxml, simplexml, spl or sqlite3' do
      expect(@app).not_to have_logged "The extension 'libxml' is not provided by this buildpack"
      expect(@app).not_to have_logged "The extension 'SimpleXML' is not provided by this buildpack"
      expect(@app).not_to have_logged "The extension 'sqlite3' is not provided by this buildpack"
      expect(@app).not_to have_logged "The extension 'SPL' is not provided by this buildpack"
    end

    it 'starts successfully and has the desired modules' do
      expect(@app).to be_running

      @browser.visit_path '/'
      expect(@browser).to have_body /module_libxml/
      expect(@browser).to have_body /module_simplexml/
      expect(@browser).to have_body /module_sqlite3/
      expect(@browser).to have_body /module_spl/
    end
  end
end

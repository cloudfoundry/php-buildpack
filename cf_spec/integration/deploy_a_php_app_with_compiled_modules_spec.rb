$: << 'cf_spec'
require 'cf_spec_helper'

describe 'deploying a basic PHP app with compiled modules in PHP_EXTENSIONS' do
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_libxml_sqlite3'
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'when the app is pushed' do
    it 'does not log an error metioning libxml or sqlite3' do
      expect(@app).not_to have_logged "The extension 'libxml' is not provided by this buildpack"
      expect(@app).not_to have_logged "The extension 'sqlite3' is not provided by this buildpack"
    end

    it 'starts successfully' do
      expect(@app).to be_running
    end
  end
end

$: << 'cf_spec'
require 'cf_spec_helper'

describe 'deploying a basic PHP app using APCu module' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'app_with_apcu'
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'after the APCu module has been loaded into PHP' do
    it 'expects CF to report the app is running' do
      expect(@app).to be_running
    end

    it 'caches a variable using APCu' do
      browser.visit_path('/')
      expect(browser).to have_body /I'm an apcu cached variable/
    end
  end
end

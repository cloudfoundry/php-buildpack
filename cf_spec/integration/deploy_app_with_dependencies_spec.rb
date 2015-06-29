$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'the application has vendored dependencies' do
    let(:app_name) { 'app_with_local_dependencies' }

    specify do
      expect(app).to be_running

      browser.visit_path('/')
      expect(browser).to have_body 'App with dependencies running'

      assert_cached_mode_has_no_internet_traffic
    end
  end
end



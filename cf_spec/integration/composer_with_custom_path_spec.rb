$: << 'cf_spec'
require 'cf_spec_helper'

describe "Composer with version set to 'latest'" do
  subject(:app) do
    Machete.deploy_app(app_name, {env:
      {'COMPOSER_PATH' => 'meatball/sub'}
    })
  end
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  let(:app_name) { 'composer_with_custom_path' }

  specify do
    expect(app).to be_running
    expect(app).to have_logged("Loading composer repositories with package information")
  end
end

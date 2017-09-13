$: << 'cf_spec'
require 'cf_spec_helper'

describe "Composer with unicode env variables" do
  let(:app_name) { 'strangechars' }
  subject(:app) do
    Machete.deploy_app(app_name, {env: {'BP_DEBUG' => 1}})
  end
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  specify do
    expect(app).to be_running
    expect(app).to have_logged('[DEBUG] composer - ENV IS: CLUSTERS_INFO={"dev01":{"env":"開発環境"')
  end
end


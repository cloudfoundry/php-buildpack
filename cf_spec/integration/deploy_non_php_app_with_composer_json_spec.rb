$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }

  after { Machete::CF::DeleteApp.new.execute(app) }

  context "deploying a non php app with composer.json file" do
    let(:app_name) { 'non_php_app_with_composer_json' }

    it 'does not detect the app' do
      expect(app).not_to be_running
      expect(app).to have_logged 'None of the buildpacks detected a compatible application'
    end
  end
end


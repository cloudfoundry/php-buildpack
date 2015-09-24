$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  subject(:app) { Machete.deploy_app(app_name) }
  let(:browser) { Machete::Browser.new(app) }

  after do
    Machete::CF::DeleteApp.new.execute(app)
  end

  context 'app has a custom extension' do
    let(:app_name) { 'php_app_with_custom_extension' }

    specify 'deploys successfully' do
      expect(app).to be_running
      expect(app).to have_logged 'https://files.phpmyadmin.net//phpMyAdmin/4.3.12/phpMyAdmin-4.3.12-english.tar.gz'
    end
  end
end




$: << 'cf_spec'
require 'cf_spec_helper'

describe 'CF PHP Buildpack' do
  let(:browser) { Machete::Browser.new(@app) }
  before(:context) do
    @app = Machete.deploy_app(
      'php_app_using_mssql',
      {env: {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    )
  end

  after(:context) do
    Machete::CF::DeleteApp.new.execute(@app)
  end

  context 'deploying a basic PHP app using mssql/freetds/pdo-dblib modules' do
    context 'after these module has been loaded into PHP' do
      it 'expects CF to report the app is running' do
        expect(@app).to be_running
      end

      it 'logs that dblib could not connect to the server' do
        expect { browser.visit_path('/') }.to raise_error(Machete::HTTPServerError)
        expect(@app).to have_logged "PHP message: PHP Fatal error:  Uncaught exception 'PDOException'"
        expect(@app).to have_logged "Unable to connect: Adaptive Server is unavailable or does not exist"
      end
    end
  end
end

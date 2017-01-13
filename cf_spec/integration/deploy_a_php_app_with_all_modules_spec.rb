$: << 'cf_spec'
require 'cf_spec_helper'
require 'yaml'

php_buildpack_manifest_file = File.join(File.expand_path(File.dirname(__FILE__)), '..', '..', 'manifest.yml')
manifest = YAML.load(File.read(php_buildpack_manifest_file))

php_modules = {}
php_modules['PHP 5'] = manifest['dependencies'].select { |dependency| dependency['name'] == "php" && dependency['version'].to_s[0] == '5' }.first
php_modules['PHP 7.0'] = manifest['dependencies'].select { |dependency| dependency['name'] == "php" && dependency['version'].to_s[0,3] == '7.0' }.first
php_modules['PHP 7.1'] = manifest['dependencies'].select { |dependency| dependency['name'] == "php" && dependency['version'].to_s[0,3] == '7.1' }.first

def setup_app(app_name)
    env_config = {env:  {'COMPOSER_GITHUB_OAUTH_TOKEN' => ENV['COMPOSER_GITHUB_OAUTH_TOKEN']}}
    deploy_app(app_name, env_config)
end


describe 'CF PHP Buildpack' do
  let(:browser)    { Machete::Browser.new(@app) }

  shared_examples_for 'it loads all the modules' do |php_version|
    it 'logs each module on the info page' do
      expect(@app).to be_running
      expect(@app).to have_logged /#{php_version}/
      browser.visit_path('/')
      php_modules[php_version]['modules'].each do |module_name|
        if module_name == 'ioncube'
          expect(browser).to have_body /ionCube&nbsp;PHP&nbsp;Loader&nbsp;\(enabled\)/
        else
          expect(browser).to have_body /module_(Zend[+ ])?#{module_name}/i
        end
      end
    end
  end

  context 'extensions are specified in .bp-config' do
    context 'deploying a basic PHP5 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_5_app_with_all_modules')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 5'
    end

    context 'deploying a basic PHP7.0 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_7_app_with_all_modules')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 7.0'
    end

    context 'deploying a basic PHP7.1 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_7_1_app_with_all_modules')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 7.1'
    end
  end

  context 'extensions are specified in composer.json' do
    context 'deploying a basic PHP5 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_5_app_with_all_modules_using_composer')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 5'
    end

    context 'deploying a basic PHP7.0 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_7_app_with_all_modules_using_composer')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 7.0'
    end

    context 'deploying a basic PHP7.1 app that loads all prepackaged extensions' do
      before(:all) do
        @app = setup_app('php_7_1_app_with_all_modules_using_composer')
      end

      after(:all) do
        Machete::CF::DeleteApp.new.execute(@app)
      end

      it_behaves_like 'it loads all the modules', 'PHP 7.1'
    end
  end
end

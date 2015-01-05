require 'bundler/setup'
require 'machete'
require 'machete/matchers'

`mkdir -p log`
Machete.logger = Machete::Logger.new("log/integration.log")

RSpec.configure do |config|
  config.after(:each) do
    expect(app.host).not_to have_internet_traffic if Machete::BuildpackMode.offline?
  end
end

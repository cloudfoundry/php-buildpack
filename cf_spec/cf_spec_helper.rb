require 'bundler/setup'
require 'machete'
require 'machete/matchers'

`mkdir -p log`
Machete.logger = Machete::Logger.new("log/integration.log")

RSpec.configure do |config|
  def assert_cached_mode_has_no_internet_traffic
    expect(app.host).not_to have_internet_traffic if Machete::BuildpackMode.cached?
  end
end

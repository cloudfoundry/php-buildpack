$: << 'cf_spec'
require 'cf_spec_helper'
require 'open3'

describe 'python unit tests' do
  let(:python_unit_test_command) { './run_tests.sh' }

  it "should all pass" do
    _, stdout, stderr, wait_thr = Open3.popen3(python_unit_test_command)
    exit_status = wait_thr.value
    unless exit_status.success?
      puts "Python Unit Tests stdout:"
      puts stdout.read
      puts "Python Unit Tests stderr:"
      puts stderr.read
    end
    expect(wait_thr.value).to eq(0)
  end
end

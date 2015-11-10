$: << 'cf_spec'
require 'cf_spec_helper'

describe 'Compile' do
  context 'when running in an unsupported stack' do
    def run(cmd, env: {})
      if RUBY_PLATFORM =~ /darwin/i
        env_flags = env.map{|k,v| "-e #{k}=#{v}"}.join(' ')
        `docker run --rm #{env_flags} -v #{Dir.pwd}:/buildpack:ro -w /buildpack cloudfoundry/cflinuxfs2 #{cmd}`
      else
        `env #{env.map{|k,v| "#{k}=#{v}"}.join(' ')} #{cmd}`
      end
    end

    it 'fails with a helpful error message' do
      output = run("./bin/compile #{Dir.mktmpdir} #{Dir.mktmpdir} 2>&1", env: {CF_STACK: 'unsupported'})
      expect(output).to include('not supported by this buildpack')
      expect($?.exitstatus).to eq 44
    end
  end
end

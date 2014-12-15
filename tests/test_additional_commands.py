from build_pack_utils import utils


extn = utils.load_extension('lib/additional_commands')


class TestAdditionalCommandsExtension(object):
    def test_no_additional_commands(self):
        ctx = {}
        tmp = extn.preprocess_commands(ctx)
        assert tmp == []

    def test_one_command_as_string(self):
        ctx = {
            'ADDITIONAL_PREPROCESS_CMDS': 'env'
        }
        tmp = extn.preprocess_commands(ctx)
        assert len(tmp) == 1
        assert tmp[0] == ['env']

    def test_one_additional_command(self):
        ctx = {
            'ADDITIONAL_PREPROCESS_CMDS': ['env']
        }
        tmp = extn.preprocess_commands(ctx)
        assert len(tmp) == 1
        assert tmp[0] == ['env']

    def test_two_additional_commands(self):
        ctx = {
            'ADDITIONAL_PREPROCESS_CMDS': ['env', 'run_something']
        }
        tmp = extn.preprocess_commands(ctx)
        assert len(tmp) == 2
        assert tmp[0] == ['env']
        assert tmp[1] == ['run_something']

    def test_command_with_arguments_as_string(self):
        ctx = {
            'ADDITIONAL_PREPROCESS_CMDS': ['echo "Hello World"']
        }
        tmp = extn.preprocess_commands(ctx)
        assert len(tmp) == 1
        assert tmp[0] == ['echo "Hello World"']

    def test_command_with_arguments_as_list(self):
        ctx = {
            'ADDITIONAL_PREPROCESS_CMDS': [['echo', '"Hello World!"']]
        }
        tmp = extn.preprocess_commands(ctx)
        assert len(tmp) == 1
        assert len(tmp[0]) == 2
        assert tmp[0][0] == 'echo'
        assert tmp[0][1] == '"Hello World!"'

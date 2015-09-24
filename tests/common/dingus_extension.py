from dingus import patch


def patches(patch_values):
    patcher_collection = PatcherCollection()

    for object_path, new_object in patch_values.iteritems():
        patcher_collection.add_patcher(patch(object_path, new_object))

    return patcher_collection


class PatcherCollection:
    def __init__(self):
        self.patchers = []

    def __enter__(self):
        for patcher in self.patchers:
            patcher.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        for patcher in self.patchers:
            patcher.__exit__(exc_type, exc_value, traceback)

    def add_patcher(self, patcher):
        self.patchers.append(patcher)

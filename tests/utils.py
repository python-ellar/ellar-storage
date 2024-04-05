import os.path
import shutil

from ellar.utils.importer import get_main_directory_by_stack

DUMB_DIRS = get_main_directory_by_stack("__main__/dumbs/", stack_level=1)
TEST_FIXTURES_DIRS = get_main_directory_by_stack("__main__/fixtures/", stack_level=1)


def clear(directory):
    try:
        shutil.rmtree(os.path.join(DUMB_DIRS, directory))
    except OSError:
        pass

from contextlib import contextmanager
from pathlib import Path
import os


@contextmanager
def manage_pwd(path: str):
    orignal_working_directory = Path.cwd()

    if not Path(path).exists():
        raise ValueError

    if not Path(path).is_dir():
        raise ValueError

    try:
        os.chdir(path)
        yield
    except ValueError:
        return
    finally:
        os.chdir(orignal_working_directory)



def directory_walk(path):
    if not Path(path).is_dir():
        yield Path(path)

    elif Path(path).is_dir():
        for path_name in Path(path).iterdir():
            if path_name.is_dir():
                yield directory_walk(path_name)
                # skip to the next item
                continue
            yield path_name

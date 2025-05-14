import logging
import os

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def get_secret(key: str, default: str = None) -> str:
    try:
        from google.colab import userdata

        try:
            value = userdata.get(key)
            print(
                f"Using {key} from colab userdata and setting corresponding os.environ value"
            )
            os.environ[key] = value
            return value
        except userdata.SecretNotFoundError:
            print(f"Using default value for {key}")
            return default
    except ImportError:
        if key in os.environ:
            print(f"Not in colab. Using {key} from environment")
            return os.environ.get(key, default)
        else:
            print(f"Using default value for {key}")
            return default

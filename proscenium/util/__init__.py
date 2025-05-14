import logging
import os

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def get_secret(key: str, default: str = None) -> str:
    try:
        from google.colab import userdata

        try:
            value = userdata.get(key)
            os.environ[key] = value
            log.info(
                f"In colab. Read {key} from colab userdata and set os.environ value"
            )
            return value
        except userdata.SecretNotFoundError:
            return default
    except ImportError:
        if key in os.environ:
            return os.environ.get(key, default)
        else:
            return default

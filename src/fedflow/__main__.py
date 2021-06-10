
import sys

from fedflow.config import Config

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "generate-config":
            if len(sys.argv) > 2:
                Config.generate_config(sys.argv[2])
            else:
                Config.generate_config(None)

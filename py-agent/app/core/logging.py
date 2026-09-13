import logging
import sys


def setup_logging():

    logging.basicConfig(
        level=logging.INFO,
        #  ??? 这种语法是有默认值吗?
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )
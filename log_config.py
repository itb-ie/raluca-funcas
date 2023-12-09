import logging
from colorlog import ColoredFormatter

# Define the formatter
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s - %(asctime)s - %(message)s",
    datefmt='%A %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white'
    }
)


def setup_logger(name, level=logging.INFO) -> logging.Logger:
    """
    Sets up the logger with the proper level and colors.
    Needed to only enable debug for my code and not the libraries that are used
    :param name: Name of the logger, use __name__
    :param level: The logger level
    :return: the logger class instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a console handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)
    return logger

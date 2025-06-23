import os
import logging
from logging import info
def setup_logging():
    """Set up logging configuration."""
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')


def main(name, exe_file, zip_file):
        setup_logging()
        output_file = os.path.join(os.getcwd(), f'{name}.exe')

        with open(output_file, 'wb') as output:
            with open(exe_file, 'rb') as f_exe:
                output.write(f_exe.read())
            with open(zip_file, 'rb') as f_zip:
                output.write(f_zip.read())

        info(f"Combined executable created: {output_file}")
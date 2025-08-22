import os
import glob
import logging
from dat_importer import import_dat_file_core

# CONFIGURATION
DAT_DIR = r"\\central_server\path\to\dat_files"  # Update this to your actual network path
IMPORTED_RECORD = r"C:\path\to\imported_dat_files.txt"  # Update this to your local record file
LOG_FILE = r"C:\path\to\import_dat_cli.log"  # Update this to your log file location

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger("import_dat_cli")

def get_imported_files():
    if not os.path.exists(IMPORTED_RECORD):
        return set()
    with open(IMPORTED_RECORD, "r") as f:
        return set(line.strip() for line in f)

def record_imported_file(filename):
    with open(IMPORTED_RECORD, "a") as f:
        f.write(filename + "\n")

def find_latest_dat_file():
    files = glob.glob(os.path.join(DAT_DIR, "*.dat"))
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest

def main():
    imported = get_imported_files()
    latest_file = find_latest_dat_file()
    if not latest_file:
        logger.info("No .dat files found.")
        print("No .dat files found.")
        return
    filename = os.path.basename(latest_file)
    if filename in imported:
        logger.info(f"{filename} already imported.")
        print(f"{filename} already imported.")
        return
    logger.info(f"Importing {filename} ...")
    result = import_dat_file_core(latest_file, logger=logger)
    record_imported_file(filename)
    logger.info(f"Imported {filename}: {result}")
    print(f"Imported {filename}. Imported: {result.get('imported_count', 0)}, Skipped: {result.get('skipped_count', 0)}, Errors: {len(result.get('errors', []))}")
    if result.get('errors'):
        print("Errors:")
        for err in result['errors']:
            print(err)

if __name__ == "__main__":
    main() 
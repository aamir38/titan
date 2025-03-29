# Titan Module Collector Tool
# Version: 1.0.0
# Last Updated: 2025-03-29
# Purpose: Collect and document all Titan modules, their functions, connections, and usage.

import os
import json
import logging


# Set up logging
logging.basicConfig(filename='Titan_Module_Master_Log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

MODULE_DIR = './'  # Adjust this to your Titan module directory


def get_all_files(directory):
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                all_files.append(os.path.join(root, file))
    return all_files


def analyze_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            return content
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None


def process_files(files):
    module_index = {}

    for file_path in files:
        file_name = os.path.basename(file_path)
        content = analyze_file(file_path)
        if content:
            module_index[file_name] = {
                'file_path': file_path,
                'content': content
            }
            logging.info(f"Analyzed: {file_name} - SUCCESS")
        else:
            logging.info(f"Analyzed: {file_name} - FAILED")

    return module_index


def save_index(module_index):
    try:
        with open('Titan_Module_Master_Index.json', 'w', encoding='utf-8') as f:
            json.dump(module_index, f, indent=2)
        logging.info("Module index successfully saved.")
    except Exception as e:
        logging.error(f"Error saving index: {e}")


if __name__ == "__main__":
    logging.info("Starting Titan Module Collector Tool...")

    files = get_all_files(MODULE_DIR)
    logging.info(f"Total Files Found: {len(files)}")

    module_index = process_files(files)

    save_index(module_index)

    logging.info("Titan Module Collection Completed. Check 'Titan_Module_Master_Log.txt' and 'Titan_Module_Master_Index.json' for details.")
    print("Collection Complete. Check the log file for details.")

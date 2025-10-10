from src.config.sqlite_connector import process_missing_data, process_duplicate_data


def transform_data():
    process_missing_and_duplicate_data()



def process_missing_and_duplicate_data():
    process_missing_data()
    process_duplicate_data()



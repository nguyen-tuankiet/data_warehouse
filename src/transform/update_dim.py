from src.config.sqlite_connector import get_airport, add_airport, get_airline, add_airline
from src.helpper.logger_config import logger

def update_dim_airport(airport_set):
    airport = set(get_airport(False))
    if not airport:
        logger.error("No airport found in database.")
        return

    difference = airport_set - airport
    if difference:
        logger.info(f"New airport found: {difference}")
        add_airport(difference)



def update_dim_airline(airline_set):
    airlines = set(get_airline(False))
    if not airlines:
        logger.error("No airlines found in database.")
        return

    difference = airline_set - airlines
    if difference:
        logger.info(f"New airport found: {difference}")
        add_airline(difference)


    pass
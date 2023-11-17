import os
from os.path import join, dirname
from decimal import Decimal
import json
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from tempfile import mkdtemp

def handler(event=None, context=None):
    """
    main driver for the lambda function.
    """
    # load necessary environment variables
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # we assume that the event payload is a JSON string, so we have to de-serialize it into a dictionary to get what we need
    raw_message = event['Records'][0]['Sns']['Message']
    # double up, since we have to escape in SNS
    message_dict = json.loads(raw_message)
    game_url = ""
    game_timestamp = ""
    failsafe = ""
    try:
        game_url = message_dict["game-url"]
        game_timestamp = message_dict["game-timestamp"]
        failsafe = message_dict["failsafe"]
    except:
        logger.info("Deserialized SNS event missing a required attribute.")
        raise

    # validate the failsafe
    if failsafe != os.environ['PERSONAL_SALT']:
        logger.info("SNS event failsafe verification did not match.")
        raise

    # connect to Dynamo
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMO_NAME'])

    # parse out the ID from the URL
    game_id = game_url.split('/')[-1]
    logger.info("Parsed game ID from SNS event: " + game_id)

    # check if the ID corresponding to the URL passed in has an existing entry in Dynamo already.
    # if it does, simply return.
    matching_id = table.get_item(Key={"game-id": game_id})
    if "Item" in matching_id:
        logger.info("SNS event URL already has an entry in DB. Skipping.")
        return

    # process the event
    logger.info("Starting game processing.")
    result_block, difficulty_selector = scrape_minesweeper_online_game(game_url)
    statistics, difficulty = process_scraped_minesweeper_game(result_block, difficulty_selector, os.environ['MINESWEEPER_USERNAME'])

    # check to see if this is meaningful (i.e., the game wasn't too short)
    if statistics["solve-percentage"] < 50.0:
        logger.info("Game processed, but solve percentage of " + str(statistics["solve-percentage"]) + " was below 50% threshold. Skipping.")
        return

    # now, actually write to Dynamo
    logger.info("Game processing complete. Writing to DB.")
    table.put_item(
        Item={
            "game-id": game_id,
            "game-timestamp": game_timestamp,
            "difficulty": difficulty,
            "elapsed-time": Decimal(str(statistics["elapsed-time"])),
            "estimated-time": Decimal(str(statistics["estimated-time"])),
            "board-solved": statistics["board-solved"],
            "completed-3bv": statistics["completed-3bv"],
            "board-3bv": statistics["board-3bv"],
            "game-3bvps": Decimal(str(statistics["game-3bvps"])),
            "useful-clicks": statistics["useful-clicks"],
            "wasted-clicks": statistics["wasted-clicks"],
            "total-clicks": statistics["total-clicks"],
            "efficiency": Decimal(str(statistics["efficiency"])),
            "solve-percentage": Decimal(str(statistics["solve-percentage"]))
        }
    )
    logger.info("Entry added to DB successfully.")
    return


def scrape_minesweeper_online_game(url):
    """
    given a URL, visits and scrapes for minesweeper game statistics.
    if no statistics are found, an exception is raised.
    returns a result block string, and html for the difficulty selector.
    """

    # if run locally, this configuration block is neded:
    '''
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService("/usr/local/bin/chromedriver")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    '''

    # in run in lambda, this configuration block is needed
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService("/opt/chromedriver")
    options.binary_location = '/opt/chrome/chrome'
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    
    driver = webdriver.Chrome(options=options, service=service)
    driver.get(url)
    # wait at MOST x seconds for rendering; if things found before then, return right away.
    # this is intentionally kept fairly low, to reduce the possibility of lambda taking forever ($$$)
    # try 8
    driver.implicitly_wait(8)

    # in the event that we've visited a URL, but haven't actually played the game at that URL,
    # there'll be no statistics to scrape.
    # in that event, quit the driver and raise an exception, which should be handled by this function's caller.
    try:
        # get the result block element. it has nicely formatted text, e.g.
        '''
        username
        Today, 09:00

        Time: 1.160 sec
        Estimated time: 75.013
        3BV: 3 / 194
        3BV/sec: 2.5862
        Clicks: 6+0
        Efficiency: 50%

        Experience: +3
        '''
        result_block = driver.find_element(By.CLASS_NAME, "result-block")
        # alternate way to find, if necessary:
        # result_block = driver.find_element(By.XPATH, "//*[@id='result_absolute_right_block']/div")
        result_block_text = result_block.text

        # get the difficulty selector element. it doesn't have nicely formatted text,
        # so get the inner HTML, e.g.
        # <span>Expert</span>&nbsp;<span class="caret"></span>
        difficulty_selector = driver.find_element(By.XPATH, "//button[@class='btn btn-sm btn-default btn-level-select dropdown-toggle']")
        # alternate way to find, if necessary:
        # difficulty_selector = driver.find_element(By.CLASS_NAME, "btn btn-sm btn-default btn-level-select dropdown-toggle")
        difficulty_selector_html = difficulty_selector.get_attribute("innerHTML")

        # quit and return
        driver.quit()
        return (result_block_text, difficulty_selector_html)
    except Exception as e:
        driver.quit()
        logger.info("Unable to scrape game.")
        raise

def process_scraped_minesweeper_game(result_block_text, difficulty_selector_html, username):
    """
    given the text from a minesweeper game result block and the html of the difficulty selector,
    parse out all relevant statistics and the actual difficulty of the game.
    verifies that the username provided is the user that played the game; raise an exception if not.
    """
    # validate the game was played by the desired user
    if username not in result_block_text:
        logger.info("Error: attempting to scrape game for another user.")
        raise
    
    # parse the difficulty from the HTML
    difficulty = ""
    if "Expert" in difficulty_selector_html:
        difficulty = "expert"
    elif "Intermediate" in difficulty_selector_html:
        difficulty = "intermediate"
    elif "Beginner" in difficulty_selector_html:
        difficulty = "beginner"
    else:
        difficulty = "other"

    # parse (and calculate) other relevant stats
    split_result_text = result_block_text.split('\n')

    # calculate time elapsed playing the game
    game_time_line = next((x for x in split_result_text if x.startswith("Time:")), "")
    elapsed_time_value = -1.0 if not game_time_line else float(game_time_line.split(' ')[1])

    # calculate the time minesweeper estimated the game would have taken
    game_estimated_time_line = next((x for x in split_result_text if x.startswith("Estimated time:")), "")
    estimated_time_value = -1.0 if not game_estimated_time_line else float(game_estimated_time_line.split(": ")[1])

    # calculate the 3bv values
    game_3bv_line = next((x for x in split_result_text if x.startswith("3BV:")), "")
    raw_3bv_value = "" if not game_3bv_line else game_3bv_line.split(": ")[1]
    board_solved = ('/' not in raw_3bv_value)
    completed_3bv_value = int(raw_3bv_value) if board_solved else int(raw_3bv_value.split(" / ")[0])
    board_3bv_value = int(raw_3bv_value) if board_solved else int(raw_3bv_value.split(" / ")[1])

    # calculate the 3bvp/s value
    game_3bvps_line = next((x for x in split_result_text if x.startswith("3BV/sec:")), "")
    the_3bvps_value = -1.0 if not game_3bvps_line else float(game_3bvps_line.split(' ')[1])

    # calculate click values
    game_clicks_line = next((x for x in split_result_text if x.startswith("Clicks:")), "")
    raw_clicks_value = "" if not game_clicks_line else game_clicks_line.split(": ")[1]
    useful_clicks_value = -1.0 if not raw_clicks_value else int(raw_clicks_value.split('+')[0])
    wasted_clicks_value = -1.0 if not raw_clicks_value else int(raw_clicks_value.split('+')[1])
    total_clicks_value = useful_clicks_value + wasted_clicks_value

    # calculate efficiency value
    game_efficiency_line = next((x for x in split_result_text if x.startswith("Efficiency:")), "")
    efficiency_string = "" if not game_efficiency_line else game_efficiency_line.split(' ')[1]
    efficiency_value = -1.0 if not efficiency_string else float(efficiency_string.strip().strip('%'))

    # calculate solved percentage
    solve_percentage_value = 100.0 if board_solved else (float(completed_3bv_value)/float(board_3bv_value)) * 100.0

    # create return objects and return
    statistics = {
        "elapsed-time": elapsed_time_value,
        "estimated-time": estimated_time_value,
        "board-solved": board_solved,
        "completed-3bv": completed_3bv_value,
        "board-3bv": board_3bv_value,
        "game-3bvps": the_3bvps_value,
        "useful-clicks": useful_clicks_value,
        "wasted-clicks": wasted_clicks_value,
        "total-clicks": total_clicks_value,
        "efficiency": efficiency_value,
        "solve-percentage": solve_percentage_value
    }
    return (statistics, difficulty)
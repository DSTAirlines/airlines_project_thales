import time
import schedule
from cron_opensky import lauch_script as lauch_opensky
from cron_airlabs import lauch_script as lauch_airlabs
from clean_mongodb import clean_data
from pipeline_aggregate import aggregate_data
from init_mongo_stats import init_data


def job_that_executes_once_opensky():
    lauch_opensky()
    return schedule.CancelJob

def job_that_executes_once_airlabs():
    lauch_airlabs()
    return schedule.CancelJob

def job_that_executes_once_stat():
    init_data()
    return schedule.CancelJob

# Create a new scheduler
scheduler1 = schedule.Scheduler()

# Add jobs to the created scheduler
scheduler1.every(30).seconds.do(job_that_executes_once_opensky)
scheduler1.every(50).seconds.do(job_that_executes_once_airlabs)
scheduler1.every(1).minutes.do(job_that_executes_once_stat)
scheduler1.every(5).minutes.do(lauch_opensky)
scheduler1.every().hour.at(":02").do(lauch_airlabs)
scheduler1.every().day.at("02:12").do(clean_data)
scheduler1.every().day.at("03:12").do(aggregate_data)


while True:
    # run_pending needs to be called on every scheduler
    scheduler1.run_pending()
    time.sleep(1)
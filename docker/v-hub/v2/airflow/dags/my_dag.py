from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
# from airflow.operators.dummy_operator import DummyOperator
# from airflow.models import Pool
from airflow.models import Variable
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path


parent_dir = str(Path(__file__).resolve().parent.parent)
functions_dir = f"{parent_dir}/functions"
sys.path.append(functions_dir)

from cron_airlabs import lauch_script as mongo_airlabs
from cron_opensky import lauch_script as mongo_opensky
from clean_mongodb import clean_data as clean_mongo
from pipeline_aggregate import aggregate_data as aggregate_mongo
from init_mongo import init_data as init_mongo_data

start_date = datetime.utcnow()


#####################################################
#   DAG
#####################################################

dag_init = DAG(
    dag_id='dag_init',
    description='Initialisation des données',
    doc_md="""## DAG de vérification de l'insertion initiale des datas,

    Vérification de l'insert initiale des datas (exécution 1 seule fois)
    * si absence de documents dans la collection data_aggregated :
      * si fichier data.json présent dans app/data_statistics : insertion des données
      * sinon : on pass
    * si absence de documents opensky :
      * appel API opensky
      * appel API airlabs
      * transform des datas
      * insert des datas dans les collections opensky et airlabs
    """,
    tags=['projet', 'datascientest', 'initialisation'],
    schedule_interval='@once',
    default_args={
        'owner': 'airflow',
        'start_date': start_date
    },
    catchup=False
)

dag_api_opensky = DAG(
    dag_id='dag_api_opensky',
    description='Appel API Opensky',
    doc_md="""## DAG d'appel API Opensky,

    Appel toutes les 5 minutes
    """,
    tags=['projet', 'datascientest', 'api_opensky'],
    schedule_interval='*/5 * * * *',
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(0)
    },
    catchup=False
)

dag_api_airlabs = DAG(
    dag_id='dag_api_airlabs',
    description='Appel API Airlabs',
    doc_md="""## DAG d'appel API Airlabs,

    Appel toutes les heures
    """,
    tags=['projet', 'datascientest', 'api_opensky'],
    schedule_interval='2 */1 * * *',
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(0)
    },
    catchup=False
)

dag_aggregate_data = DAG(
    dag_id='dag_aggregate_data',
    description='Pipeline d\'agrégration des données',
    doc_md="""## Pipeline d'agrégration des données

    Appel une fois par jour ; à 1h30
    """,
    tags=['projet', 'datascientest', 'data_aggregated'],
    schedule_interval='22 1 * * *',
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(0)
    },
    catchup=False
)

dag_clean_data = DAG(
    dag_id='dag_clean_data',
    description='Suppression des données de plus de 7 jours',
    doc_md="""## Suppression des anciennes données

    * Durée de rétention des data de 7 jours

    Appel une fois par jour ; à 2h30
    """,
    tags=['projet', 'datascientest', 'data_cleaned'],
    schedule_interval='22 0 * * *',
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(0)
    },
    catchup=False
)


def initialization_data():
    init_mongo_data()
    Variable.set("init_data", True)

def mongo_opensky_task():
    test = Variable.get("init_data", None)
    if test is None:
        initialization_data()
    mongo_opensky()

def mongo_airlabs_task():
    test = Variable.get("init_data", None)
    if test is None:
        initialization_data()
    mongo_airlabs()

def clean_mongo_task():
    test = Variable.get("init_data", None)
    if test is None:
        initialization_data()
    clean_mongo()

def aggregate_mongo_task():
    test = Variable.get("init_data", None)
    if test is None:
        initialization_data()
    aggregate_mongo()



#####################################################
#   TASKS
#####################################################

# DAG INIT - Tâche 1 : Initialisation
task_init = PythonOperator(
    task_id='task_init_data',
    python_callable=initialization_data,
    retries=3,
    retry_delay=timedelta(seconds=10),
    doc = '''Initaliser les données - Insert data si collections vides''',
    pool_slots=1,
    dag=dag_init
)

# DAG OPENSKY - Tâche 1 : Appel API Opensky
task_opensky = PythonOperator(
    task_id='task_opensky',
    python_callable=mongo_opensky_task,
    retries=15,
    retry_delay=timedelta(seconds=10),
    doc = '''Appel API Opensky''',
    pool_slots=1,
    dag=dag_api_opensky
)

# DAG AIRLABS - Tâche 1 : Appel API Airlabs
task_airlabs = PythonOperator(
    task_id='task_airlabs',
    python_callable=mongo_airlabs_task,
    retries=20,
    retry_delay=timedelta(seconds=10),
    doc = '''Appel API Airlabs''',
    pool_slots=1,
    dag=dag_api_airlabs
)

# DAG AGGREGATE - Tâche 1 : Pipeline d'agrégration des données
task_aggregate = PythonOperator(
    task_id='task_aggregate',
    python_callable=aggregate_mongo_task,
    retries=3,
    retry_delay=timedelta(seconds=10),
    doc = '''Pipeline d'agrégration des données''',
    pool_slots=1,
    dag=dag_aggregate_data
)

# DAG CLEAN - Tâche 1 : Suppression des anciennes données
task_clean = PythonOperator(
    task_id='task_clean',
    python_callable=clean_mongo_task,
    retries=3,
    retry_delay=timedelta(seconds=10),
    doc = '''Suppression des anciennes données''',
    pool_slots=1,
    dag=dag_clean_data
)



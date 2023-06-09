#!/bin/bash

# docker-compose down --volumes --rmi all
# Arrêt des containers en fonctionnement
echo ""
echo "########################################################################"
echo "# Arrêt des containers en fonctionnement"
echo "########################################################################"
echo ""
docker container stop $(docker ps -a -q)

# Suppression des containers présents
echo ""
echo "########################################################################"
echo "# Suppression des containers présents"
echo "########################################################################"
echo ""
docker container rm -f $(docker ps -a -q)

# Suppression des images présentes
echo ""
echo "########################################################################"
echo "# Suppression des images présentes"
echo "########################################################################"

echo ""
docker image rm -f $(docker images -a -q)

# Suppression des volumes présents
echo ""
echo "########################################################################"
echo "# Suppression des volumes présents"
echo "########################################################################"
echo ""
docker volume rm -f $(docker volume ls -q)


# Airflow
echo ""
echo "########################################################################"
echo "# Préparation Airflow"
echo "########################################################################"
echo ""
echo "Test existence du dossier airflow..."
airflow_folder="./airflow"
if [ -d "$airflow_folder" ]; then
  rm -rf "$airflow_folder"
  echo "- Suppression du dossier $airflow_folder"
else
  echo "- Le dossier $airflow_folder n'existe pas"
fi
echo "Création des dossiers /dags /logs /plugins /functions..."
mkdir airflow
mkdir ./airflow/dags ./airflow/logs ./airflow/plugins ./airflow/functions
echo "Ajout des variables d'environnement Airflow..."
new_airflow_uid=$(id -u)
new_airflow_gid=0
sed -i "s/^AIRFLOW_UID=.*/AIRFLOW_UID=${new_airflow_uid}/" ./.env
sed -i "s/^AIRFLOW_GID=.*/AIRFLOW_GID=${new_airflow_gid}/" ./.env
echo ""

# Initialisation Airflow
echo ""
echo "########################################################################"
echo "# Initialisation Airflow..."
echo "########################################################################"
echo ""
docker-compose up airflow-init
echo "Copie du fichier DAG dans le dossier /dags..."
cp my_dag.py ./airflow/dags
echo  "Copie du dossier /functions dans le dossier /airflow..."
cp -r functions/* ./airflow/functions/

# Build et lancement des containers
echo ""
echo "########################################################################"
echo "# Build et lancement des containers"
echo "########################################################################"
echo ""
docker-compose up -d --build
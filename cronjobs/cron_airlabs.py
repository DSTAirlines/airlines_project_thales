#!/usr/bin/python3
import sys
from pathlib import Path

# Ajout du path du projet
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(f"{parent_dir}/live_api")

# Importer le fichier de connexion à MongoDB
from fetch_airlabs_data import lauch_script

lauch_script()

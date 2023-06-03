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
# docker-compose down --volumes --rmi all

# Suppression des volumes présents
echo ""
echo "########################################################################"
echo "# Suppression des volumes présents"
echo "########################################################################"
echo ""
docker volume rm -f $(docker volume ls -q)

# Build et lancement des containers
echo ""
echo "########################################################################"
echo "# Build et lancement des containers"
echo "########################################################################"
echo ""
docker-compose up -d --build
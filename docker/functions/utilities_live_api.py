from datetime import datetime
import pytz

def convert_time_unix_utc_to_datetime_fr(time_unix_utc):

    # Convertir le timestamp Unix en objet datetime UTC
    utc_datetime = datetime.utcfromtimestamp(time_unix_utc)

    # Définir le fuseau horaire français
    paris_tz = pytz.timezone("Europe/Paris")

    # Convertir l'objet datetime UTC en objet datetime avec le fuseau horaire français
    local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(paris_tz)

    # Formater l'objet datetime en chaîne de caractères
    datetime_fr = local_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return datetime_fr

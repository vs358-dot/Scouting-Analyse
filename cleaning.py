import pandas as pd
from datetime import datetime
import numpy as np
import re

# Groß-und Kleinschreibung des Begriffs 'Ausland' verheinheitlichen
def normalize_status(s):
    if pd.isna(s):
        return None
    s_str = str(s).strip()
    # "ausland" → "Ausland", egal ob groß/klein
    return re.sub(r'ausland', 'Ausland', s_str, flags=re.IGNORECASE)

def clean_data(df):
    """
    Datenbereinigung und -vereinheitlichung für hochgeladene Dateien
    in der Streamlit-App.
    
    Ziel:
    Vorbereitung der Rohdaten für spätere Analysen.
    """
    df = df.copy()
    
    # Sicherstellen, dass die Spalte "Profi geworden" existiert
    # Falls nicht vorhanden, wird sie mit dem Defaultwert "nein" ergänzt
    if "Profi geworden" not in df.columns:
        df["Profi geworden"] = "nein"
        
    # Vereinheitlichung der Spalte "Im Verein" (Leerzeichen entfernen, alles in Kleinbuchstaben)
    df["Im Verein"] = df["Im Verein"].astype(str).str.strip().str.lower()

    # Datumsumwandlung: ungültige Einträge werden zu NaT    
    df["Privatspielberechtigt seit"] = pd.to_datetime(
        df["Privatspielberechtigt seit"], errors="coerce"
    )

    df["Abmeldedatum"] = pd.to_datetime(
        df["Abmeldedatum"], errors="coerce"
    )
    
    # Setzen des Abmeldedatums auf das heutige Datum, falls die Person aktuell noch im Verein ist
    heute = pd.Timestamp(datetime.now().date())
    heute = pd.Timestamp(datetime.now().date())
    df.loc[
        df["Im Verein"].astype(str).str.strip().str.lower().isin(["ja", "0"]),
        "Abmeldedatum"
    ] = heute
        
    df = df.replace("0", np.nan)
    df = df.dropna(subset=[
        "Privatspielberechtigt seit",
        "Abmeldedatum"
    ])
    
    df["Abmeldedatum"] = pd.to_datetime(df["Abmeldedatum"], errors="coerce")
    
    # Berechnung der Aufenthaltsdauer im Verein (in Tagen)
    df["Tagesdifferenz"] = (df["Abmeldedatum"] - df["Privatspielberechtigt seit"]).dt.days


    # Geburtsdatum vereinheitlichen
    df["Geburtsdatum"] = df["Geburtsdatum"].astype(str)

    # Geburtsjahr extrahieren
    def extract_birthyear(text):
        if not text or text.lower() == "nan":
            return None
        text = text.strip()
        for part in [text[:4], text[-4:]]:
            try:
                year = int(part)
                if 1900 <= year <= 2025:
                    return year
            except:
                pass
        return None

    df["Geburtsjahr"] = df["Geburtsdatum"].apply(extract_birthyear)
    
    # Vereinheitlichung der Status-Spalten (falls vorhanden)
    if "Status2" in df.columns:
       df["Status2"] = df["Status2"].apply(normalize_status)
      
    if "Status" in df.columns:
       df["Status"] = df["Status"].apply(normalize_status)


    # Ordnung der Eintrittsstufen als geordnete kategoriale Variable
    stufen_order = ["U08","U09","U10","U11","U12","U13","U14","U15","U16","U17","U19","U21/U23"]
    df["im Verein seit"] = pd.Categorical(df["im Verein seit"], categories=stufen_order, ordered=True)

    return df

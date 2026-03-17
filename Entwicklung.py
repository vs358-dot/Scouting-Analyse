import streamlit as st
import pandas as pd
import plotly.express as px
from cleaning import clean_data

def entwicklung():
    """
    Diese Funktion stellt die Analyse-Seite „Entwicklung nach Vereinswechsel“ dar.
    
    Zweck der Seite:
    - Analyse der sportlichen Entwicklung von Spielern während ihrer Zeit beim FCA
    - Vergleich des Status beim Eintritt (Status) mit dem Status beim neuen Verein (Status2)
    - Untersuchung des Zusammenhangs zwischen Verweildauer im Verein
      und der späteren Entwicklung (Verbesserung, Gleichstand, Verschlechterung)
    - Visualisierung der Ergebnisse mittels Boxplot und Histogramm
    
    Berücksichtigt werden ausschließlich Spieler,
    die den Verein bereits verlassen haben.
    """
    
    #Seitentitel
    st.title("Verweildauer × Status")

    # Prüfen, ob eine Spielerliste geladen wurde
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()
        
    # Daten bereinigen und vorbereiten
    df = clean_data(st.session_state["players_df"])
    df = df[df["Im Verein"]== "nein"]
    
    # Sidebar-Filter
    # -----------------------------------------------------
    st.sidebar.header("Filter")

    # Im Verein seit → als Dropdown
    stufen_order = ["U08","U09","U10","U11","U12","U13","U14","U15","U16","U17","U19","U21/U23"]
    selected_stufe = st.sidebar.selectbox("Im Verein seit:", ["Alle"] + stufen_order)
    
    if selected_stufe != "Alle":
        df = df[df["im Verein seit"].astype(str).str.lower() == selected_stufe.lower()]

    # Verweildauer Einheit
    y_unit = st.sidebar.selectbox("Verweildauer anzeigen in:", ["Tage", "Monate", "Jahre"])
    
    # Jahrgang
    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    geburtsjahr = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))
    df = df[(df["Geburtsjahr"] >= geburtsjahr[0]) & (df["Geburtsjahr"] <= geburtsjahr[1])]
    
      
    # Mitglied in Jahr
    df["start_year"] = df["Privatspielberechtigt seit"].dt.year
    df["end_year"] = df["Abmeldedatum"].dt.year
    
    year_min = int(df["start_year"].min())
    year_max = int(df["end_year"].max())
    
    selected_range = st.sidebar.slider(
        "Mitglied im Verein im Zeitraum",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )
    
    df = df[
        (df["start_year"] <= selected_range[1]) &
        (df["end_year"] >= selected_range[0])
    ]
    
    # -----------------------------------------------------
    
    # Verweildauer umrechnen
    if y_unit == "Monate":
        df["Verweildauer"] = df["Tagesdifferenz"] / 30
    elif y_unit == "Jahre":
        df["Verweildauer"] = df["Tagesdifferenz"] / 365
    else:
        df["Verweildauer"] = df["Tagesdifferenz"]

    # Mapping Status → Rang
    mapping = {
        "Profiliga": 1,
        "Profiliga (ausland)": 1,
        "NLZ": 2,
        "NLZ (ausland)": 2,
        "BFV-NLZ": 2,
        "regional": 3
    }

    # Nur Zeilen mit beiden Statuswerten verwenden
    df = df.dropna(subset=["Status", "Status2"])
    
    # Status in numerische Ränge umwandeln
    df["rank1"] = df["Status"].map(mapping)
    df["rank2"] = df["Status2"].map(mapping)
    df = df.dropna(subset=["rank1", "rank2"])

    # Entwicklung berechnen
    #  1  → Verbesserung
    #  0  → gleiches Niveau
    # -1  → Verschlechterung
    df["entwicklung"] = df.apply(
        lambda x: 0 if x["rank1"] == x["rank2"]
                  else 1 if x["rank2"] < x["rank1"]
                  else -1,
        axis=1
    )

    df = df.drop(columns=["rank1", "rank2"])
    df["entwicklung"] = df["entwicklung"].astype(int)
    
    # Sicherstellen, dass die Verweildauer numerisch ist
    df["Tagesdifferenz"] = pd.to_numeric(df["Tagesdifferenz"], errors="coerce")
    df = df.dropna(subset=["Tagesdifferenz"])
    
    # Abbruch, falls keine Daten übrig bleiben
    if df.empty:
        st.warning("Keine Daten für die gewählte Filterkombination.")
        return

    # Vollständiger Name für Hover-Anzeige
    df["Name"] = df["Vorname"].astype(str) + " " + df["Nachname"].astype(str)


    # Boxplot
    # -----------------------------
    fig_box = px.box(
        df,
        x="entwicklung",
        y="Verweildauer",
        points="all",
        hover_data={
            "Name": True,
            "Verweildauer": True,
            "entwicklung": False,
        },
        labels={
            "entwicklung": "Entwicklung (-1=schlechter, 0=gleich, 1=besser)",
            "Verweildauer": f"Verweildauer ({y_unit})"
        },
        title="Verweildauer vs. Entwicklungsstatus"
    )

    st.plotly_chart(fig_box, use_container_width=True)
    # -----------------------------
    
    
    # Histogramm / Top 10 Vereine
    # -----------------------------
    df_top1 = df[df["entwicklung"] == 1]
    if not df_top1.empty and "abgebender Verein" in df_top1.columns:
        # Gruppieren nach Verein
        top_vereine = (
            df_top1["abgebender Verein"]
            .value_counts()
            .nlargest(10)
            .index.tolist()
        )
        df_top1 = df_top1[df_top1["abgebender Verein"].isin(top_vereine)]

        fig_hist = px.histogram(
            df_top1,
            x="abgebender Verein",
            title="Top 10 abgegebene Vereine, aus denen die meisten Spieler sich verbessert haben",
            labels={"abgebender Verein": "Abgegebener Verein", "count": "Anzahl Spieler"},
            color_discrete_sequence=["darkblue"]
        )

        fig_hist.update_layout(
            xaxis_title="Abgegebener Verein",
            yaxis_title="Anzahl Spieler",
            xaxis=dict(categoryorder="total descending")
        )

        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Keine Spieler mit Entwicklung=1 oder Spalte 'abgegebener Verein' fehlt.")
    # -----------------------------------------------------      
    
    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden alle Zeilen, die einen der folgenden Werte nicht enthalten, entfernt:<br>"
        "Geburtsjahr, Status, Status2 oder Im Verein seit.<br>"
        "Der Filter <i>Mitglied im Verein im Zeitraum</i> filtert nach Spielern, die in mindestens einem der ausgewählten Jahre im FCA gespielt haben.</sub>",
        unsafe_allow_html=True
    )

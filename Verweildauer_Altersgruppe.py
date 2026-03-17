import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from cleaning import clean_data

def verweildauer_altersgruppe():
    """
        Diese Funktion stellt die Analyse-Seite „Verweildauer × Altersgruppe“ dar.
        
        Zweck der Seite:
        - Analyse der Verweildauer von Spielern im Verein
          in Abhängigkeit vom Eintrittsalter (Altersstufe)
        - Bereitstellung interaktiver Filter (Im Verein, Status, Jahrgang)
        - Visualisierung der Daten mittels Histogramm und Scatterplot
        - Optionale Hervorhebung von Profiliga-Spielern und Mittelwerten
        
        Die Funktion greift auf die zuvor hochgeladene und bereinigte
        Spielerliste aus dem Streamlit session_state zu.
    """
    
    #Seitentitel
    st.title("Verweildauer × Altersgruppe")
    
    # Abbruch, falls noch keine Spielerliste geladen wurde
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()

    # Bereinigung
    df = clean_data(st.session_state["players_df"])

    # Filter (Sidebar) definieren
    # ------------------------------------
    st.sidebar.header("Filter")

    verein_list = ["Alle"] + sorted(df["Im Verein"].dropna().unique())
    selected_verein = st.sidebar.selectbox("Im Verein:", verein_list)
    
    status_list = ["Alle"] + sorted(df["Status"].dropna().unique())
    selected_status = st.sidebar.selectbox("Status:", status_list)

    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    jahrgang = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))

    y_unit = st.sidebar.selectbox("Verweildauer anzeigen in:", ["Tage", "Monate", "Jahre"])

    profiliga_separat = st.sidebar.checkbox("Profiliga-Spieler als Stern anzeigen")
    mittelwertpunkte = st.sidebar.checkbox("Mittelwertpunkte anzeigen")
    # ------------------------------------
    
    # Filter anwenden
    # ------------------------------------
    df = df.dropna(subset=["Geburtsjahr", "Privatspielberechtigt seit",
                           "Im Verein", "im Verein seit"])

    if selected_verein != "Alle":
        df = df[df["Im Verein"].str.lower() == selected_verein.lower()]
    if selected_status != "Alle":
        df = df[df["Status"].astype(str).str.lower() == selected_status.lower()]

    df = df[(df["Geburtsjahr"] >= jahrgang[0]) & (df["Geburtsjahr"] <= jahrgang[1])]
    # ------------------------------------
    

    # Umrechnung der Tagesdifferenz in die gewünschte Einheit
    if y_unit == "Monate":
        df["Verweildauer"] = df["Tagesdifferenz"] / 30
    elif y_unit == "Jahre":
        df["Verweildauer"] = df["Tagesdifferenz"] / 365
    else:
        df["Verweildauer"] = df["Tagesdifferenz"]

    # Vollständiger Name für Hover-Anzeige
    df["Name"] = df["Vorname"].astype(str) + " " + df["Nachname"].astype(str)


    # Definierte Reihenfolge der Altersstufen
    stufen_order = ["U08","U09","U10","U11","U12","U13","U14","U15","U16","U17","U19","U21/U23"]
    # Umwandlung in kategorische Variable mit fester Sortierung
    df["im Verein seit"] = df["im Verein seit"].astype(str).str.strip()
    df["im Verein seit"] = pd.Categorical(df["im Verein seit"],
                                          categories=stufen_order,
                                          ordered=True)

    # Histogramm
    # ------------------------------------
    st.subheader("Histogramm – Häufigkeiten Eintrittsalter")

    hist = px.histogram(
        df,
        x="im Verein seit",
        category_orders={"im Verein seit": stufen_order},
        color_discrete_sequence=["steelblue"]
    )
    st.plotly_chart(hist, use_container_width=True)
    # ------------------------------------

    # Scatterplot
    # ------------------------------------
    st.subheader("Scatterplot – Verweildauer")
    # Standarddarstellung ohne Trennung von Profiliga-Spielern
    if not profiliga_separat:
        fig = px.scatter(
            df,
            x="im Verein seit",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )
    # Trennung von Profiliga- und Nicht-Profiliga-Spielern
    else:
        nicht_profi = df[
            (~df["Status2"].astype(str).str.contains("Profiliga", na=False)) &
            (df["Profi geworden"] == "nein")
        ]
        
        profi = df[
            (df["Status2"].astype(str).str.contains("Profiliga", na=False)) |
            (df["Profi geworden"] == "ja")
        ]
        fig = px.scatter(
            nicht_profi,
            x="im Verein seit",
            y="Verweildauer",
            hover_name="Name",
            color_discrete_sequence=["green"]
        )

        fig.add_scatter(
            x=profi["im Verein seit"],
            y=profi["Verweildauer"],
            mode="markers",
            marker=dict(symbol="star", size=10, color="red"),
            hoverinfo="text",
            hovertext=[
                f"{r['Name']}<br>{y_unit}: {r['Verweildauer']:.1f}"
                for _, r in profi.iterrows()
            ]
        )

    # Mittelwertpunkte (optional)
    if mittelwertpunkte:
        mean_df = df.groupby("im Verein seit")["Verweildauer"].mean().reset_index()
        mean_df["im Verein seit"] = pd.Categorical(mean_df["im Verein seit"],
                                                   categories=stufen_order,
                                                   ordered=True)

        fig.add_scatter(
            x=mean_df["im Verein seit"],
            y=mean_df["Verweildauer"],
            mode="markers",
            marker=dict(symbol="x", size=12, color="orange"),
            name="Mittelwert"
        )
    # Achsentitel und Sortierung
    fig.update_layout(
        xaxis_title="Im Verein seit",
        yaxis_title=f"Verweildauer ({y_unit})",
        showlegend=False
    )
    fig.update_xaxes(categoryorder="array", categoryarray=stufen_order)

    st.plotly_chart(fig, use_container_width=True)
    # ------------------------------------

    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden alle Zeilen, die einen der folgenden Werte nicht enthalten, entfernt:<br> "
        "Geburtsjahr, Im Verein seit, Im Verein.<br>"
        "Als Profispieler werden alle Spieler gezählt, deren Status2 Profiliga ist oder für die Profi geworden = ja gilt.</sub>",
        unsafe_allow_html=True
    )


import streamlit as st
import pandas as pd
import plotly.express as px
from cleaning import clean_data


def zugaenge():
    """
        Diese Funktion stellt die Analyse-Seite „Zugänge – Analyse abgebender Vereine“ dar.
        
        Zweck der Seite:
        - Analyse, aus welchen Vereinen Spieler zum aktuellen Verein gewechselt sind
        - Untersuchung der Zugänge nach:
            • abgebendem Verein
            • Entwicklungsbereich beim Eintritt
            • Verpflichtungszeitraum
            • Verweildauer im Verein
        - Bereitstellung umfangreicher Filter zur gezielten Auswertung
        - Visualisierung der Ergebnisse mit Balkendiagrammen
        
        Die Seite greift auf die bereinigte Spielerliste aus dem Streamlit
        session_state zu.
    """
    
    #Seitentitel
    st.title("Zugänge – Analyse abgebender Vereine")


    # Prüfen, ob Upload vorhanden ist
    if "players_df" not in st.session_state:
        st.error("Bitte zuerst eine Spielerliste hochladen.")
        st.stop()

    df = clean_data(st.session_state["players_df"]).copy()

    # Ungültige Zeilen entfernen
    df = df.dropna(subset=[ "abgebender Verein", "im Verein seit"])

    # Entwicklungsbereiche definieren
    grundlagen = ["U8", "U9", "U10", "U11"]
    aufbau = ["U12", "U13", "U14", "U15"]
    leistungs = ["U16", "U17", "U18", "U19", "U21/U23"]

    def bereich(u):
        """
        Ordnet eine Altersstufe einem Entwicklungsbereich zu.
        """
        if u in grundlagen:
            return "Grundlagenbereich (U8–U11)"
        elif u in aufbau:
            return "Aufbaubereich (U12–U15)"
        elif u in leistungs:
            return "Leistungsbereich (U16–U23)"
        return None

    # Neue Spalte für den Entwicklungsbereich
    df["Entwicklungsbereich"] = df["im Verein seit"].apply(bereich)

    # Verpflichtungszeitraum
    def verpflichtungs_kategorie(datum):
        """
        Kategorisiert das Eintrittsdatum in feste Zeiträume.
        """
        if pd.isna(datum):
            return None
        if datum >= pd.Timestamp("2021-07-01"):
            return ">= 01.07.2021"
        elif datum <= pd.Timestamp("2017-06-30"):
            return "<= 30.06.2017"
        return "01.07.2017-30.06.2021"
    
    # Neue Spalte für den Verpflichtungszeitraum
    df["Verpflichtungszeitraum"] = df["Privatspielberechtigt seit"].apply(verpflichtungs_kategorie)

    # -----------------------------------------------------
    # Sidebar Filter
    st.sidebar.header("Filter")

    entwicklung_sel = st.sidebar.selectbox(
        "Entwicklungsbereich:",
        ["Alle", "Grundlagenbereich (U8–U11)", "Aufbaubereich (U12–U15)", "Leistungsbereich (U16–U23)"]
    )

    zeit_sel = st.sidebar.selectbox(
        "Verpflichtungszeitraum:",
        ["Alle", "<= 30.06.2017", "01.07.2017-30.06.2021", ">= 01.07.2021"]
    )
    
    status_list = ["Alle"] + sorted(df["Status"].dropna().unique())
    selected_status = st.sidebar.selectbox("Status:", status_list)
    
    # Jahrgang
    min_y, max_y = int(df["Geburtsjahr"].min()), int(df["Geburtsjahr"].max())
    jahrgang = st.sidebar.slider("Geburtsjahr:", min_y, max_y, (min_y, max_y))

    min_v, max_v = int(df["Tagesdifferenz"].min()), int(df["Tagesdifferenz"].max())
    verweil = st.sidebar.slider("Verweildauer (Tage):", min_v, max_v, (min_v, max_v))
    
    # Mindestanzahl an Spielern pro Verein
    min_spieler = st.sidebar.number_input(
        "Mindestanzahl der Spieler pro Verein (für Verweildauer-Analyse):",
        min_value=1,
        value=1,
        step=1
    )
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Filter anwenden
    df = df[(df["Tagesdifferenz"] >= verweil[0]) & (df["Tagesdifferenz"] <= verweil[1])]

    if entwicklung_sel != "Alle":
        df = df[df["Entwicklungsbereich"] == entwicklung_sel]

    if zeit_sel != "Alle":
        df = df[df["Verpflichtungszeitraum"] == zeit_sel]
    
    if selected_status != "Alle":
        df = df[df["Status"].astype(str).str.lower() == selected_status.lower()]
        
    df = df[(df["Geburtsjahr"] >= jahrgang[0]) & (df["Geburtsjahr"] <= jahrgang[1])]
    # -----------------------------------------------------
    
    # -----------------------------------------------------
    # Top-10 Histogramm – Abgebende Vereine
    st.subheader("Top 10 – Abgebende Vereine")

    if df.empty:
        st.warning("Keine Daten für diese Filterkombination.")
        return

    top10 = df["abgebender Verein"].value_counts().head(10).reset_index()
    top10.columns = ["abgebender Verein", "Anzahl"]

    # Reihenfolge speichern → Grundlage für alle weiteren Plots
    vereins_order = top10["abgebender Verein"].tolist()

    fig = px.bar(
        top10,
        x="abgebender Verein",
        y="Anzahl",
        category_orders={"abgebender Verein": vereins_order},
        color_discrete_sequence=["steelblue"],
        title="Top 10 abgebende Vereine"
    )

    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)


    # Subset der relevanten Vereine für die grouped charts
    df_top10 = df[df["abgebender Verein"].isin(vereins_order)].copy()
    df_top10["abgebender Verein"] = pd.Categorical(
        df_top10["abgebender Verein"], categories=vereins_order, ordered=True
    )
    
    # -----------------------------------------------------
    # Grouped Chart 1 – Entwicklungsbereich × Verein

    st.subheader("Abgebende Vereine × Entwicklungsbereich")

    df_grouped1 = (
        df_top10
        .groupby(["abgebender Verein", "Entwicklungsbereich"])
        .size()
        .reset_index(name="Anzahl")
    )
    
    fig_group1 = px.bar(
        df_grouped1,
        x="abgebender Verein",
        y="Anzahl",
        color="Entwicklungsbereich",
        barmode="group",
        category_orders={"abgebender Verein": vereins_order},
        title="Spielerzugänge nach Entwicklungsbereich (Top 10)"
    )
    
    fig_group1.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_group1, use_container_width=True)
    # -----------------------------------------------------
    
    # -----------------------------------------------------
    # Grouped Chart 2 – Verpflichtungszeitraum × Verein
    st.subheader("Abgebende Vereine × Verpflichtungszeitraum")

    df_grouped2 = (
        df_top10
        .groupby(["abgebender Verein", "Verpflichtungszeitraum"])
        .size()
        .reset_index(name="Anzahl")
    )
    
    fig_group2 = px.bar(
        df_grouped2,
        x="abgebender Verein",
        y="Anzahl",
        color="Verpflichtungszeitraum",
        barmode="group",
        category_orders={"abgebender Verein": vereins_order},
        title="Spielerzugänge nach Verpflichtungszeitraum (Top 10)"
    )
    fig_group2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_group2, use_container_width=True)
    # -----------------------------------------------------
    # -----------------------------------------------------
    
    # -----------------------------------------------------
    # Histogramm 2 – Durchschnittliche Verweildauer

    st.subheader("Verweildauer – Vereine mit der höchsten durchschnittlichen Verweildauer")
    # Alle Vereine zählen
    verein_counts = df.groupby("abgebender Verein").size()
    
    # Nur Vereine mit mindestens min_spieler Spielern
    vereine_fuer_verweildauer = verein_counts[verein_counts >= min_spieler].index
    
    df_verweildauer = df[df["abgebender Verein"].isin(vereine_fuer_verweildauer)]
    
    # Durchschnittliche Verweildauer berechnen
    df_verweildauer_agg = (
        df_verweildauer.groupby("abgebender Verein")
        .agg(
            Verweildauer_Tage=("Tagesdifferenz", "mean"),
            Spieleranzahl=("Tagesdifferenz", "count")
        )
        .sort_values("Verweildauer_Tage", ascending=False)
        .head(10)
        .reset_index()
    )
    
    
    fig2 = px.bar(
        df_verweildauer_agg,
        x="abgebender Verein",
        y="Verweildauer_Tage",
        color_discrete_sequence=["indianred"],
        title="Top 10 Vereine nach durchschnittlicher Verweildauer",
        hover_data={"Verweildauer_Tage": ":.1f", "Spieleranzahl": True}
    )
    
    fig2.update_layout(
        xaxis_title="Abgebender Verein",
        yaxis_title="Durchschnittliche Verweildauer (Tage)",
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    # -----------------------------------------------------
    
    
    # Fußnote
    st.markdown(
        "<sub>Für diese Analysen wurden Zeilen ohne Werte in "
        "<i>abgebender Verein</i> oder <i>im Verein seit</i> entfernt.</sub>",
        unsafe_allow_html=True
    )

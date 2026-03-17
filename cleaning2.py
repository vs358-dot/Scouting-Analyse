# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 17:23:51 2025

@author: veren
"""

def clean_data(df):
    df = df.copy()

    rename_map = {
        df.columns[0]: "Vorname",
        df.columns[1]: "Nachname",
        df.columns[2]: "Geburtsdatum"
    }

    df = df.rename(columns=rename_map)

    return df

import numpy as np
import pandas as pd
from main import haversine
from main import Kenngroessen
from main import glaette_gps

def test_haversine_zero_distance():
    d = haversine(48.0, 11.0, 48.0, 11.0) # Distanz zwischen identischen Punkten muss 0 sein.
    assert np.isclose(d, 0.0)


def test_haversine_one_degree_latitude():
    d = haversine(0.0, 0.0, 1.0, 0.0) # 1° Breitendifferenz entspricht ungefähr 111 km.
    assert np.isclose(d, 111195, atol=300)


def test_haversine_symmetric():
    # Die Distanz muss symmetrisch sein.
    d1 = haversine(48.0, 11.0, 49.0, 10.0)
    d2 = haversine(49.0, 10.0, 48.0, 11.0)
    assert np.isclose(d1, d2)


def test_haversine_vectorized():
    lat1 = np.array([0, 0])
    lon1 = np.array([0, 0])
    lat2 = np.array([1, 2])
    lon2 = np.array([0, 0])
    d = haversine(lat1, lon1, lat2, lon2)
    assert len(d) == 2
    assert d[1] > d[0]


def test_kenngroessen():
    df = pd.DataFrame({
        "P": [100, 200, 150],
        "ds": [10, 20, 30],
        "v": [2, 4, 6],
        "time": [0, 5, 10],
        "ele": [100, 110, 105]
    })
    result = Kenngroessen(df)
    assert result["P_max"] == 200
    assert result["Gesamtstrecke"] == 60
    assert result["Durchschnittsgeschwindigkeit"] == 4
    assert result["Gesamtzeit"] == 10
    assert result["Anstieg"] == 10
    assert result["Abstieg"] == 5


def test_glaette_gps_creates_columns():
    df = pd.DataFrame({
        "lat": np.arange(20),
        "lon": np.arange(20),
        "ele": np.arange(20)
    })
    result = glaette_gps(df)
    assert "lat_glatt" in result.columns
    assert "lon_glatt" in result.columns
    assert "ele_glatt" in result.columns

def test_glaette_gps_mean():
    df = pd.DataFrame({
        "lat": np.arange(10),
        "lon": np.arange(10),
        "ele": np.arange(10)
    })
    result = glaette_gps(df)
    assert np.isclose(result.loc[9, "lat_glatt"], 4.5)
    assert np.isclose(result.loc[9, "lon_glatt"], 4.5)
    assert np.isclose(result.loc[9, "ele_glatt"], 4.5)

def test_glaette_gps_length():
    df = pd.DataFrame({
        "lat": np.random.rand(50),
        "lon": np.random.rand(50),
        "ele": np.random.rand(50)
    })
    result = glaette_gps(df)
    assert len(result) == len(df)


def test_glaette_gps_original_dataframe():
    df = pd.DataFrame({
        "lat": [1, 2, 3],
        "lon": [4, 5, 6],
        "ele": [7, 8, 9]
    })
    result = glaette_gps(df)
    assert "lat_glatt" not in df.columns
    assert "lon_glatt" not in df.columns
    assert "ele_glatt" not in df.columns
    assert "lat_glatt" in result.columns


def test_kenngroessen_keys():
    df = pd.DataFrame({
        "P": [1],
        "ds": [1],
        "v": [1],
        "time": [0],
        "ele": [0]
    })
    result = Kenngroessen(df)
    assert set(result.keys()) == {
        "P_max",
        "Gesamtstrecke",
        "Durchschnittsgeschwindigkeit",
        "Gesamtzeit",
        "Anstieg",
        "Abstieg"
    }
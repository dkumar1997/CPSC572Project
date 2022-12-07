from regex import I
import requests
import json
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib as mpl

def get_data(method, params):
  api_base = 'http://airlabs.co/api/v9/'
  api_result = requests.get(api_base+method, params)
  return api_result.json()

def get_routes(airport_code):  
  params = {
  'api_key': '9fb7d70b-aa4d-4841-9ea6-de822a9b7eae',
  'iata_code': airport_code
  }
  return get_data('airports', params)

def normalize_data(response):
  return pd.json_normalize(response["response"])
  
def get_all_routes():
  airport_codes = pd.read_excel('airports.xlsx', usecols="C")
  cleaned_airport_codes = [x for x in airport_codes["iata_code"].tolist() if str(x) != 'nan']

  data_frames = []

  for airport_code in cleaned_airport_codes:
    response = get_routes(airport_code)
    data_frame = normalize_data(response)
    data_frames.append(data_frame)

  result = pd.concat(data_frames)
  result.to_excel("routes.xlsx")

def number_of_nodes_and_edges():
  routes = pd.read_excel('routes.xlsx', usecols="J,O")
  iata_codes = routes['dep_iata'].tolist() + routes['arr_iata'].to_list()
  print(list(set(iata_codes)))
  nodes = len(list(set(iata_codes)))
  edges = routes.groupby(['dep_iata', 'arr_iata']).size()
  return nodes, edges

def build_nodes_file():
  routes = pd.read_excel('all_routes_canada_and_out.xlsx', usecols="J,O")
  iata_codes = routes['dep_iata'].tolist() + routes['arr_iata'].to_list()
  no_duplicats_iata_codes = list(set(iata_codes))
  airports_dataframe = pd.DataFrame({"iata_code": no_duplicats_iata_codes})
  airports_dataframe.to_excel("nodes_updated.xlsx")

def build_edges_file():
  routes = pd.read_excel('all_routes_canada_and_out.xlsx', usecols="J:U")
  edges = routes.groupby(['dep_iata', 'arr_iata', 'days'], as_index=False).size()
  final_data = []
  for index, row in edges.iterrows():
    number_of_days = len(row['days'].split(","))
    number_of_flights = number_of_days * row['size']
    final_data.append([row['dep_iata'], row['arr_iata'],number_of_flights])

  final_data_frame = pd.DataFrame(final_data, columns=['source', 'target', 'weight'])
  merge_sum = final_data_frame.groupby(['source', 'target'], as_index=False).sum()
  merge_sum.to_excel("edges_updated.xlsx")

def convert_edges_to_id():
  nodes = pd.read_excel("nodes_updated.xlsx")
  edges = pd.read_excel("edges_updated.xlsx")
  node_dictionary = dict(zip(nodes.iata_code, nodes.id))
  final_data = []
  for index, row in edges.iterrows():
    final_data.append([node_dictionary[row["source"]], node_dictionary[row["target"]], row["weight"]])
  
  final_data_frame = pd.DataFrame(final_data, columns=['source', 'target', 'weight'])
  final_data_frame.to_excel("edges_indexed_updated.xlsx")

def non_canadian_airports():
  canada_airport_codes = pd.read_excel('airports.xlsx', usecols="C")
  cleaned_airport_canada_codes = [x for x in canada_airport_codes["iata_code"].tolist() if str(x) != 'nan']
  routes = pd.read_excel('routes.xlsx', usecols="J,O")
  all_iata_codes = routes['dep_iata'].tolist() + routes['arr_iata'].to_list()
  cleaned_all_iata_codes = list(set(all_iata_codes))
  outside_of_canada_airports = [x for x in cleaned_all_iata_codes if x not in cleaned_airport_canada_codes]
  return outside_of_canada_airports, cleaned_airport_canada_codes

def non_canadian_airport_routes_to_canada():
  non_canada_airports, canada_airports = non_canadian_airports()
  data_frames = []

  for airport_code in non_canada_airports:
    print(airport_code)
    response = get_routes(airport_code)
    data_frame = normalize_data(response)
    if not data_frame.empty:
      print("wasn't empty")
      data_frame_canada_arrival = data_frame[data_frame['arr_iata'].isin(canada_airports)]
      data_frames.append(data_frame_canada_arrival)

  result = pd.concat(data_frames)
  result.to_excel("routes_into_canada.xlsx")


def combine_all_routes():
  canada_and_out_routes = pd.read_excel('routes.xlsx', usecols='B:X')
  out_into_canada_routes = pd.read_excel('routes_into_canada.xlsx', usecols='B:X')
  result = pd.concat([canada_and_out_routes,out_into_canada_routes])
  result.to_excel('all_routes_canada_and_out.xlsx')

def final_form():
  convert_edges_to_id()

def input_long_and_lat():
  airports = pd.read_excel('nodes_updated.xlsx')
  airports["Latitude"] = ""
  airports["Longitude"] = ""


  for index, row in airports.iterrows():
    response = get_routes(row['Label'])
    data_frame = normalize_data(response)
    airports.at[index,'Latitude'] = data_frame.at[0,'lat']
    airports.at[index,'Longitude'] = data_frame.at[0,'lng']
    
  airports.to_excel('lat_and_long_nodes.xlsx')


def drawing_visuals():
  nodes = pd.read_excel('lat_and_long_nodes.xlsx')
  edges = pd.read_excel('edges_indexed_updated.xlsx')

  graph = nx.DiGraph()

  for index, row in nodes.iterrows():
    graph.add_node(row['id'], label=row['Label'], lat=row['lat'], long=row['lng'])
  
  
  for index, row in edges.iterrows():
    graph.add_edge(row['target'], row['source'], weight=row['weight'])
    
  fig = plt.figure(figsize=(8,8))
  nx.draw_spring(graph, node_size=40)
  
  


drawing_visuals()


  




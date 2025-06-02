import os
import sys
from algo_flow import generate_preference_schedule_from_csv
from collections import defaultdict

os.makedirs("result", exist_ok=True)

input_csv = "./data/loc_data_with_specializations.csv"
input_json = "./data/rooms_locations_updated.json"

for week in range(1, 4):
    output_file = f"./result/flow_output_schedule_week_{week}.txt"
    generate_preference_schedule_from_csv(input_csv, input_json, output_file, defaultdict(int), week)


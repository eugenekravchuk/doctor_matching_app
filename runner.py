import os
import sys
from algo_flow import generate_preference_schedule_from_csv, change_weekly_schedule
from collections import defaultdict

os.makedirs("result", exist_ok=True)

input_csv = "./data/loc_data_simplified.csv"
input_json = "./data/rooms_locations_updated.json"
weekly_sched = "./data/week_1.txt"
deleted_shifts = {'Костюк О. В.': [(1, 1)], 'Горічко І.В.': [(2, 1)], 'Бойко (Сулима) А.М.': [(2, 1)]}

change_weekly_schedule(input_csv, input_json, weekly_sched, deleted_shifts)
# generate_preference_schedule_from_csv(input_csv, input_json, output_file, defaultdict(int), de)


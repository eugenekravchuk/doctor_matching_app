import pandas as pd
import networkx as nx
import itertools
import sys
import os
import json
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from maximum_flow_impl import min_cost_max_flow

def split_data(data_str, delim=','):
    return [elem.strip() for elem in data_str.split(delim)]

def distribute_evenly(number, parts = 4):
    if not number:
        return [0] * parts

    result = [number // parts] * parts
    for i in range(number % parts):
        result[i] += 1
    return result

def get_obligatory_shifts(df_input, week):
    obl_shifts = split_data(df_input)
    res = set()

    for data in obl_shifts:

        if not data:
            continue
        
        data = data.split('|')
        if data[2][0] == str(week):
            res.add((data[0], data[1], tuple(map(int, data[2][2:].split('.')))))

    return res

def reverse_schedule_dict(schedule):
    reversed_schedule = {}
    for loc, cab_data in schedule.items():
        for cab, shifts in cab_data.items():
            for shift, doctor in shifts.items():
                if doctor is not None:
                    if doctor not in reversed_schedule:
                        reversed_schedule[doctor] = set()
                    reversed_schedule[doctor].add((loc, cab, shift))
    return reversed_schedule


def calculate_necessary_allocations(df, all_shift_ids, loc_cabs_dict, week, doctor_penalty):

    G = nx.DiGraph()
    source, sink = 'S', 'T'
    G.add_node(source, type='source')
    G.add_node(sink, type='sink')
    costs = {}
    cabinet_penalty = defaultdict(int)
    necessary_shifts = {}
    schedule = {}

    expected_flow = 0

    for loc in loc_cabs_dict:
        for spec in loc_cabs_dict[loc]:
            for cab in loc_cabs_dict[loc][spec]:
                cabinet_penalty[(loc, cab)] = 0
                for shift in all_shift_ids:
                    schedule.setdefault(loc, {}).setdefault(cab, {})
                    schedule[loc][cab][shift] = None
                    G.add_node((loc, cab, shift), type='loc_cab_shift')
                    G.add_edge((loc, cab, shift), sink, capacity=1)

    for _, row in df.iterrows():

        doctor = row['Doctor']
        costs[doctor] = {}

        specs = split_data(row['Specialization'])
        locs = split_data(row['Cabinets'])

        min_shifts = distribute_evenly(int(row['MinShifts']) if pd.notna(row['MinShifts']) else 0)[week - 1]
        expected_flow += min_shifts

        forbidden = set(split_data(row['ForbiddenShifts'])) if pd.notna(row['ForbiddenShifts']) else set()
        forbidden = set(tuple(map(int, data.split('.')[1:])) for data in forbidden if data[0] == str(week))

        necessary_shifts[doctor] = get_obligatory_shifts(row['RequiredShifts'] if pd.notna(row['RequiredShifts']) else '', week)

        G.add_node(doctor, type='doctor')
        G.add_edge(source, doctor, capacity=min_shifts)

        for shift in all_shift_ids:
            if shift in forbidden:
                continue
            G.add_node((doctor, shift), type='doctor_shift')
            G.add_edge(doctor, (doctor, shift), capacity=1)

        for i, loc in enumerate(locs):

            if loc not in costs:
                costs[loc] = {}

            costs[doctor][loc] = costs[loc][doctor] = 5*i + 1

            for spec in specs:
                if loc in loc_cabs_dict and spec in loc_cabs_dict[loc]:
                    for cab in loc_cabs_dict[loc][spec]:
                        for shift in all_shift_ids:
                            if shift in forbidden:
                                continue
                            G.add_edge((doctor, shift), (loc, cab, shift), capacity=1)

    flow, _, schedule = min_cost_max_flow(G, costs, doctor_penalty, cabinet_penalty, necessary_shifts, schedule, source, sink)

    if flow != expected_flow:
        print(f"Warning: Expected flow {expected_flow}, but got {flow}. Not all doctors may be assigned their minimum shifts.")
    else:
        print('Minimum requirements satisfied')
    
    return reverse_schedule_dict(schedule)


def generate_preference_schedule_from_csv(input_csv_path: str, loc_cabs_path: str, output_path: str, doctor_penalty: dict, week) -> str:
    
    df = pd.read_csv(input_csv_path)

    days, shifts = range(1, 8), range(1, 3)
    all_shift_ids = [(d, s) for d, s in itertools.product(days, shifts)]

    with open(loc_cabs_path, 'r', encoding='utf-8') as f:
        loc_cabs_data = json.load(f)
        loc_cabs_dict = {}

        for elem in loc_cabs_data:
            loc = elem['location']
            cabinets = elem['room']
            spec = elem['specialization']
            if not loc in loc_cabs_dict:
                loc_cabs_dict[loc] = {}

            loc_cabs_dict[loc][spec] = split_data(cabinets)

    required = calculate_necessary_allocations(df, all_shift_ids, loc_cabs_dict, week, doctor_penalty)

    G = nx.DiGraph()
    source, sink = 'S', 'T'
    G.add_node(source, type='source')
    G.add_node(sink, type='sink')
    costs = {}
    cabinet_penalty = defaultdict(int)
    schedule = {}

    for loc in loc_cabs_dict:
        for spec in loc_cabs_dict[loc]:
            for cab in loc_cabs_dict[loc][spec]:
                cabinet_penalty[(loc, cab)] = 0
                for shift in all_shift_ids:
                    schedule.setdefault(loc, {}).setdefault(cab, {})
                    schedule[loc][cab][shift] = None
                    G.add_node((loc, cab, shift), type='loc_cab_shift')
                    G.add_edge((loc, cab, shift), sink, capacity=1)

    for _, row in df.iterrows():

        doctor = row['Doctor']
        costs[doctor] = {}

        specs = split_data(row['Specialization'])
        locs = split_data(row['Cabinets'])

        max_shifts = distribute_evenly(int(row['MaxShifts']) if pd.notna(row['MaxShifts']) else 4 * len(all_shift_ids))[week - 1]

        forbidden = set(split_data(row['ForbiddenShifts'])) if pd.notna(row['ForbiddenShifts']) else set()
        forbidden = set(tuple(map(int, data.split('.')[1:])) for data in forbidden if data[0] == str(week))

        G.add_node(doctor, type='doctor')
        G.add_edge(source, doctor, capacity=max_shifts)

        for shift in all_shift_ids:
            if shift in forbidden:
                continue
            G.add_node((doctor, shift), type='doctor_shift')
            G.add_edge(doctor, (doctor, shift), capacity=1)

        for i, loc in enumerate(locs):

            if loc not in costs:
                costs[loc] = {}

            costs[doctor][loc] = costs[loc][doctor] = 5*i + 1

            for spec in specs:
                if loc in loc_cabs_dict and spec in loc_cabs_dict[loc]:
                    for cab in loc_cabs_dict[loc][spec]:
                        for shift in all_shift_ids:
                            if shift in forbidden:
                                continue
                            G.add_edge((doctor, shift), (loc, cab, shift), capacity=1)

    _, _, schedule = min_cost_max_flow(G, costs, doctor_penalty, cabinet_penalty, required, schedule, source, sink)

    with open(output_path, "w", encoding="utf-8") as f:
        for loc in sorted(schedule.keys()):
            f.write(f"Локація: {loc}\n")
            f.write("="*40 + "\n")
            
            for cab in sorted(schedule[loc].keys()):
                f.write(f"Кабінет: {cab}\n")
                f.write("-"*30 + "\n")
                
                for shift in all_shift_ids:
                    assigned = schedule[loc][cab].get(shift, "Немає лікаря")
                    f.write(f"{shift} - {assigned}\n")
                
                f.write("-"*30 + "\n")
    
    return schedule

def generate_monthly_schedule_from_csv(input_csv_path: str, loc_cabs_path: str, output_path: str) -> str:

    df = pd.read_csv(input_csv_path)
    doctors = {row['Doctor']: int(row['Fine']) for _, row in df.iterrows()}
    doctor_penalty = {doctor: 4 if not fine else 0 for doctor, fine in doctors.items()}

    for week in range(1, 5):

        out_res = output_path + f"week_{week}.txt"

        schedule = generate_preference_schedule_from_csv(input_csv_path, loc_cabs_path, out_res, doctor_penalty, week)
        for loc in schedule:
            for cab in schedule[loc]:
                for shift in schedule[loc][cab]:
                    if schedule[loc][cab][shift] is not None:
                        doctor_penalty[schedule[loc][cab][shift]] += 0.5
        
        for doctor in doctor_penalty:
            if not doctors[doctor]:
                doctor_penalty[doctor] *= 1.2
    
    print('Generated monthly schedule')


def change_weekly_schedule(input_csv_path: str, loc_cabs_path: str, weekly_schedule_path: str, deleted_shifts: dict) -> str:
    df = pd.read_csv(input_csv_path)
    week = int(weekly_schedule_path.split('_')[-1][0])
    with open(weekly_schedule_path, 'r', encoding='utf-8') as f:
        weekly_schedule = f.read().splitlines()
        current_schedule = {}
        shifts_to_change = set()
        necessary_set = set()
        exp_flow = 0

        current_location, current_cab = None, None
        for line in weekly_schedule:
            if line.startswith("Локація:"):
                current_location = line.replace("Локація: ", "").strip()
            elif line.startswith("Кабінет:"):
                current_cab = line.replace("Кабінет: ", "").strip()
            elif line.startswith("-") or line.startswith("="):
                continue
            else:
                shift, doctor = line.split(" - ")

                if doctor == "None" or doctor == "Немає лікаря":
                    continue

                exp_flow += 1
                shift = tuple(map(int, shift[1:-1].split(',')))

                if doctor in deleted_shifts and shift in deleted_shifts[doctor]:
                    shifts_to_change.add((current_location, current_cab, shift))
                    continue

                if doctor not in current_schedule:
                    current_schedule[doctor] = set()
                
                current_schedule[doctor].add((current_location, current_cab, shift))
                necessary_set.add((current_location, current_cab, shift))
    
    with open(loc_cabs_path, 'r', encoding='utf-8') as f:
        loc_cabs_data = json.load(f)
        loc_cabs_dict = {}

        for elem in loc_cabs_data:
            loc = elem['location']
            cabinets = elem['room']
            spec = elem['specialization']
            if not loc in loc_cabs_dict:
                loc_cabs_dict[loc] = {}

            loc_cabs_dict[loc][spec] = split_data(cabinets)

    costs = {}
    days, shifts = range(1, 8), range(1, 3)
    all_shift_ids = [(d, s) for d, s in itertools.product(days, shifts)]
    G = nx.DiGraph()
    source, sink = 'S', 'T'
    G.add_node(source, type='source')
    G.add_node(sink, type='sink')
    cabinet_penalty = defaultdict(int)
    doctor_penalty = {}
    schedule = {}

    for loc in loc_cabs_dict:
        for spec in loc_cabs_dict[loc]:
            for cab in loc_cabs_dict[loc][spec]:
                cabinet_penalty[(loc, cab)] = 0
                for shift in all_shift_ids:
                    schedule.setdefault(loc, {}).setdefault(cab, {})
                    schedule[loc][cab][shift] = None

                    if (loc, cab, shift) in shifts_to_change or (loc, cab, shift) in necessary_set:
                        G.add_node((loc, cab, shift), type='loc_cab_shift')
                        G.add_edge((loc, cab, shift), sink, capacity=1)

    doctors = {row['Doctor']: int(row['Fine']) for _, row in df.iterrows()}
    for doc, fine in doctors.items():
        doctor_penalty[doc] = len(current_schedule.get(doc, set())) / 2
        doctor_penalty[doc] += 4 if not fine else 0

    for _, row in df.iterrows():

        doctor = row['Doctor']
        costs[doctor] = {}

        specs = split_data(row['Specialization'])
        locs = split_data(row['Cabinets'])

        max_shifts = distribute_evenly(int(row['MaxShifts']) if pd.notna(row['MaxShifts']) else 4 * len(all_shift_ids))[week - 1]

        if doctor in deleted_shifts:
            max_shifts = len(current_schedule.get(doctor, set()))

        forbidden = set(split_data(row['ForbiddenShifts'])) if pd.notna(row['ForbiddenShifts']) else set()
        forbidden = set(tuple(map(int, data.split('.')[1:])) for data in forbidden if data[0] == str(week))

        G.add_node(doctor, type='doctor')
        G.add_edge(source, doctor, capacity=max_shifts)

        for shift in all_shift_ids:
            if shift in forbidden or (doctor in deleted_shifts and shift in deleted_shifts[doctor]):
                continue
            G.add_node((doctor, shift), type='doctor_shift')
            G.add_edge(doctor, (doctor, shift), capacity=1)

        for i, loc in enumerate(locs):

            if loc not in costs:
                costs[loc] = {}

            costs[doctor][loc] = costs[loc][doctor] = 5*i + 1

            for spec in specs:
                if loc in loc_cabs_dict and spec in loc_cabs_dict[loc]:
                    for cab in loc_cabs_dict[loc][spec]:
                        for shift in all_shift_ids:
                            if shift in forbidden or (doctor in deleted_shifts and shift in deleted_shifts[doctor]):
                                continue

                            if (loc, cab, shift) in shifts_to_change:
                                G.add_edge((doctor, shift), (loc, cab, shift), capacity=1)

                            if doctor in current_schedule and (loc, cab, shift) in current_schedule[doctor]:
                                G.add_edge((doctor, shift), (loc, cab, shift), capacity=1)

    flow, _, schedule = min_cost_max_flow(G, costs, doctor_penalty, cabinet_penalty, current_schedule, schedule, source, sink)

    if flow < exp_flow:
        print(f"Warning: Expected flow {exp_flow}, but got {flow}. Not all shifts have a suitable replacement.")

    with open(weekly_schedule_path, "w", encoding="utf-8") as f:
        for loc in sorted(schedule.keys()):
            f.write(f"Локація: {loc}\n")
            f.write("="*40 + "\n")
            
            for cab in sorted(schedule[loc].keys()):
                f.write(f"Кабінет: {cab}\n")
                f.write("-"*30 + "\n")
                
                for shift in all_shift_ids:
                    assigned = schedule[loc][cab].get(shift, "Немає лікаря")
                    f.write(f"{shift} - {assigned}\n")
                
                f.write("-"*30 + "\n")


if __name__ == "__main__":
    input_csv_path = "./data/new_data/loc_data_simplified.csv"
    loc_cabs_path = "./data/new_data/rooms_locations_updated.json"
    output_path = "./result/"
    week_path = "./result/week_1.txt"
    generate_monthly_schedule_from_csv(input_csv_path, loc_cabs_path, output_path)
    # change_weekly_schedule(input_csv_path, loc_cabs_path, week_path, {'Горічко І.В.': {(3, 1)}})
        
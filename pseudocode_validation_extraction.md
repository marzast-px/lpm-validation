# Pseudocode: Validation Dataset Extraction (Procedural)

## Overview
Extract validation data from S3 simulation results and compile into CSV files per car.

**Process Flow:**
1. **Discovery**: Extract metadata from geometry folders
2. **Results Extraction**: Match geometries with results and extract data
3. **Summary Report**: Generate report showing results availability per car
4. **Export**: Save data to CSV files

**Discovery Stage Purpose:**
1. Traverse all geometry folders in S3 (flat structure, no simulator hierarchy)
2. Extract metadata from JSON files in each geometry folder:
   - Car name
   - Car group (from car_groups_dict)
   - Baseline ID
   - Morph type
   - Morph parameter value
3. Create simulation records capturing all available geometry variants

## Parameters
`s3_bucket`, `geometries_prefix`, `results_prefix`, `output_path`, `car_groups_dict`, `aws_profile`

## Data Structure

```
S3 Geometries: geometry_folder/simulation_info.json
  → JSON contains: car_name, baseline_id, morph_type, morph_parameter_value
  → Car group derived from car_groups_dict
S3 Results: {simulation_prefix}_results/[export_scalars.json, export_force_series.json]

Note: Geometries folder contains all geometry variants. No simulator hierarchy at this level.
```

## Main Algorithm

```
FUNCTION extract_validation_data(...):
    s3_client = create_s3_client(aws_profile)
    simulation_data = []
    
    # 1. Discovery - Extract metadata from all geometry folders
    FOR geometry_folder IN list_s3_folders(geometries_prefix):
        # Extract metadata from JSON in this geometry folder
        json_data = find_and_load_json(geometry_folder)
        
        # Create simulation record with geometry metadata
        sim_record = {
            "car_name": json_data.get("car_name"),
            "car_group": car_groups_dict.get(json_data.get("car_name"), "unknown"),
            "baseline_id": json_data.get("baseline_id"),
            "morph_type": json_data.get("morph_type"),
            "morph_value": json_data.get("morph_parameter_value"),
            "geometry_name": extract_name(geometry_folder)
        }
        simulation_data.append(sim_record)
    
    # 2. Extract Results - Match simulation records with results and extract data
    FOR sim_record IN simulation_data:
        # Find matching result folder for this geometry
        result_folder = find_result_folder_s3(results_prefix, sim_record["geometry_name"])
        
        IF result_folder EXISTS:
            # Load results data
            scalars = load_json_from_s3(result_folder + "/export_scalars.json")
            force_series = load_json_from_s3(result_folder + "/export_force_series.json")
            
            # Extract and update simulation record
            sim_record["converged"] = check_convergence(scalars)
            sim_record["coefficients"] = extract_force_coefficients(scalars)
            sim_record["avg_forces"] = compute_averaged_forces(force_series)
            sim_record["metrics"] = compute_statistical_metrics(force_series)
            sim_record["has_results"] = True
        ELSE:
            sim_record["has_results"] = False
    
    # 3. Generate Summary Report
    summary_report = generate_results_summary(simulation_data)
    print_report(summary_report)
    save_report(summary_report, output_path + "/validation_summary.txt")
    
    # 4. Export
    FOR car_name, records IN group_by_car(simulation_data):
        write_to_csv(f"{output_path}/{car_name}_validation_data.csv", records)
END
```

## Helper Functions

```
# S3 Access
list_s3_folders(prefix) → List folders with pagination
load_json_from_s3(s3_key) → Parse JSON from S3

# Discovery Stage
find_and_load_json(geometry_folder) → Find JSON file and extract metadata
  → Returns: {car_name, baseline_id, morph_type, morph_parameter_value}

# Results Extraction
find_result_folder_s3(prefix, name) → Match geometry to results by prefix
extract_force_coefficients(data) → Cd, Cl, Cs, Cd_front, Cl_front, Cl_rear
check_convergence(data) → Boolean
compute_averaged_forces(series) → avg_fx, avg_fy, avg_fz (over last 20% window)
compute_statistical_metrics(series) → std_fx/fy/fz, max/min_fx

# Export
group_by_car(records) → Dictionary grouped by car_name
write_to_csv(filename, records) → CSV with all columns

# Reporting
generate_results_summary(simulation_data) → Summary report
  → For each car: total simulations, results available, results missing
  → Returns: {car_name: {total: N, with_results: M, missing: K}}
print_report(summary) → Display report to console
save_report(summary, filepath) → Save report to file
```

## CSV Output

```
Columns: Name, Morph_Type, Morph_Value, Baseline_ID, Converged, 
         Cd, Cl, Cs, Cd_front, Cl_front, Cl_rear, 
         Avg_Fx, Avg_Fy, Avg_Fz, Std_Fx, Std_Fy, Std_Fz

Output: One CSV per car → {car_name}_{simulator}.csv
```

## Validation Summary Report

```
Example Output:

Validation Results Summary
==========================
Car: Audi_RS7
  Total Simulations: 30
  Results Available: 5
  Results Missing: 25
  Completion: 16.7%

Car: BMW_X5
  Total Simulations: 28
  Results Available: 28
  Results Missing: 0
  Completion: 100%

Overall:
  Total Simulations: 58
  Results Available: 33
  Results Missing: 25
  Overall Completion: 56.9%
```

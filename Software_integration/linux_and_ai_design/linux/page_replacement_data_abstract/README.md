# Linux Page Replacement Data Collection

## Project Structure
page_replacement_project/
├── scripts/ # Collection and analysis scripts
│ ├── collect_basic_data.sh
│ ├── run_workloads.sh
│ ├── stop_workloads.sh
│ └── analyze_basic_data.sh
├── workloads/ # Memory workload generators
│ ├── sequential_access.c
│ ├── random_access.c
│ └── mixed_workload.c
├── data/ # Collected data (auto-created)
├── logs/ # Workload logs (auto-created)
└── run_experiment.sh # Main controller
## Quick Start

1. **Make all scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   chmod +x run_experiment.sh

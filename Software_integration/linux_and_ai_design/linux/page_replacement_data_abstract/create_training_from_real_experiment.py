#!/usr/bin/env python3
import json
import random
import numpy as np

def create_training_data_from_real_results():
    """
    Create training data based on Shubham's actual experiment results:
    - Started: 6,453,748 minor faults
    - Ended: 6,942,149 minor faults  
    - Duration: 269 seconds
    - Fault increase: 488,401 faults (≈1816 faults/second)
    - Memory available: 6.3GB to 6.8GB fluctuations
    - Major faults: 15,945 to 15,965 (slow increase)
    """
    
    print("Creating training data from REAL experiment results...")
    print("Based on your actual data:")
    print("- 488,401 page faults over 269 seconds")
    print("- Memory fluctuations: 6.3GB to 6.8GB available")
    print("- Workloads: Sequential, Random, Mixed patterns")
    
    training_sequences = []
    
    # Real statistics from your experiment
    base_faults = 6453748
    final_faults = 6942149
    total_fault_increase = final_faults - base_faults
    faults_per_second = total_fault_increase / 269  # ≈1816 faults/second
    
    base_major_faults = 15945
    final_major_faults = 15965
    
    # Create multiple training sequences simulating different scenarios
    for sequence_id in range(1000):
        # Choose a pattern type based on your workloads
        pattern_type = random.choice(["sequential", "random", "mixed", "locality"])
        
        # Simulate different starting points in your experiment
        start_offset = random.randint(0, 200)  # Start at different times
        current_base_faults = base_faults + int(start_offset * faults_per_second)
        
        # Create a history sequence (what the AI sees)
        history_length = random.randint(20, 40)
        memory_history = []
        
        for step in range(history_length):
            # Realistic fault progression based on your data
            time_offset = start_offset + step
            current_faults = current_base_faults + int(step * faults_per_second * random.uniform(0.8, 1.2))
            
            # Realistic memory fluctuations based on your data (6.3GB-6.8GB)
            mem_available = random.randint(6300000, 6800000)
            mem_pressure = 1.0 - (mem_available / 8388608)  # Assuming 8GB total
            
            # Major faults slowly increasing
            current_major = base_major_faults + int((final_major_faults - base_major_faults) * (time_offset / 269))
            
            memory_history.append({
                'pgfault': current_faults,
                'pgmajfault': current_major,
                'mem_available': mem_available,
                'mem_pressure': mem_pressure,
                'timestep': step
            })
        
        # Generate page access pattern based on workload type
        page_sequence = generate_workload_pattern(pattern_type, 50)
        
        # Predict next state (what the AI should predict)
        next_time_offset = start_offset + history_length
        next_faults = current_base_faults + int(next_time_offset * faults_per_second)
        next_mem_available = random.randint(6300000, 6800000)
        next_major = base_major_faults + int((final_major_faults - base_major_faults) * (next_time_offset / 269))
        
        # Next pages to predict (based on pattern)
        next_pages = predict_next_pages(pattern_type, page_sequence)
        
        # Trust factors for your hybrid system
        trust_factors = {
            'pattern_confidence': calculate_pattern_confidence(pattern_type),
            'memory_stability': random.uniform(0.7, 0.9),
            'historical_accuracy': random.uniform(0.6, 0.85),
            'current_pressure': memory_history[-1]['mem_pressure'] if memory_history else 0.3
        }
        
        training_sequence = {
            'sequence_id': sequence_id,
            'pattern_type': pattern_type,
            'memory_history': memory_history,
            'page_access_pattern': page_sequence,
            'targets': {
                'next_page_faults': next_faults,
                'next_major_faults': next_major,
                'next_memory_available': next_mem_available,
                'next_pages': next_pages,
                'next_memory_pressure': 1.0 - (next_mem_available / 8388608)
            },
            'trust_factors': trust_factors,
            'metadata': {
                'based_on_real_experiment': True,
                'real_fault_range': [base_faults, final_faults],
                'real_duration_seconds': 269,
                'real_fault_increase': total_fault_increase
            }
        }
        
        training_sequences.append(training_sequence)
    
    return training_sequences

def generate_workload_pattern(pattern_type, length):
    """Generate page access patterns based on your actual workloads"""
    sequence = []
    current_page = random.randint(0, 1000)
    
    if pattern_type == "sequential":
        # Like your sequential_access workload
        for i in range(length):
            sequence.append(current_page)
            current_page = (current_page + 1) % 1000
            
    elif pattern_type == "random":
        # Like your random_access workload
        for i in range(length):
            sequence.append(random.randint(0, 1000))
            
    elif pattern_type == "mixed":
        # Like your mixed_workload
        for i in range(length):
            if random.random() < 0.7:  # 70% sequential
                sequence.append(current_page)
                current_page = (current_page + 1) % 1000
            else:  # 30% random jumps
                sequence.append(random.randint(500, 1500))  # Different range
                
    else:  # locality
        # Spatial locality pattern
        base_page = random.randint(0, 800)
        for i in range(length):
            # Access pages within a local window
            sequence.append(base_page + random.randint(0, 200))
            # Occasionally jump to new locality
            if random.random() < 0.02:  # 2% chance to jump
                base_page = random.randint(0, 800)
    
    return sequence

def predict_next_pages(pattern_type, current_sequence):
    """Predict next pages based on pattern (what your AI should learn)"""
    if not current_sequence:
        return []
    
    if pattern_type == "sequential":
        last_page = current_sequence[-1]
        return [(last_page + i + 1) % 1000 for i in range(5)]
        
    elif pattern_type == "random":
        # Hard to predict truly random, but might have some locality
        return [random.randint(0, 1000) for _ in range(5)]
        
    elif pattern_type == "mixed":
        last_page = current_sequence[-1]
        # Mix of sequential and random predictions
        next_pages = []
        for i in range(5):
            if random.random() < 0.6:  # 60% chance sequential
                next_pages.append((last_page + i + 1) % 1000)
            else:
                next_pages.append(random.randint(0, 1000))
        return next_pages
        
    else:  # locality
        # Predict pages in the same locality
        last_page = current_sequence[-1]
        base = last_page - (last_page % 256)  # Assume 256-page localities
        return [base + random.randint(0, 255) for _ in range(5)]

def calculate_pattern_confidence(pattern_type):
    """Calculate how confident we can be in predictions for this pattern"""
    confidence_map = {
        "sequential": 0.9,    # Easy to predict
        "locality": 0.8,      # Fairly predictable
        "mixed": 0.6,         # Somewhat predictable
        "random": 0.3         # Hard to predict
    }
    return confidence_map.get(pattern_type, 0.5)

def main():
    print("=== CREATING AI TRAINING DATA FROM REAL EXPERIMENT ===")
    print("Using your actual page fault statistics and memory patterns")
    print()
    
    training_data = create_training_data_from_real_results()
    
    # Save the training data
    output_file = "real_experiment_training_data.json"
    with open(output_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print(f"✓ Created {len(training_data)} training sequences")
    print(f"✓ Based on your real experiment results")
    print(f"✓ Saved to: {output_file}")
    
    # Show statistics
    pattern_counts = {}
    for seq in training_data:
        pattern = seq['pattern_type']
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    print(f"\n=== TRAINING DATA COMPOSITION ===")
    for pattern, count in pattern_counts.items():
        print(f"{pattern:12}: {count:4} sequences")
    
    # Show a sample sequence
    if training_data:
        sample = training_data[0]
        print(f"\n=== SAMPLE TRAINING SEQUENCE ===")
        print(f"Pattern: {sample['pattern_type']}")
        print(f"Memory history: {len(sample['memory_history'])} steps")
        print(f"First memory step - Faults: {sample['memory_history'][0]['pgfault']}, Pressure: {sample['memory_history'][0]['mem_pressure']:.3f}")
        print(f"Last memory step - Faults: {sample['memory_history'][-1]['pgfault']}, Pressure: {sample['memory_history'][-1]['mem_pressure']:.3f}")
        print(f"Page sequence length: {len(sample['page_access_pattern'])}")
        print(f"Target - Next faults: {sample['targets']['next_page_faults']}")
        print(f"Trust factors: {sample['trust_factors']}")

if __name__ == "__main__":
    main()

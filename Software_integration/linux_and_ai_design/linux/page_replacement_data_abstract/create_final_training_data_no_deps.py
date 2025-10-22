#!/usr/bin/env python3
import json
import random
import math

def generate_training_data_based_on_real_experiment():
    """
    Generate complete training data based on Shubham's real Linux VM experiment
    No external dependencies required - uses only Python standard library
    """
    
    print("=== Generating AI Training Data from Real Experiment ===")
    print("Based on your actual results:")
    print("- 488,401 page faults over 269 seconds")
    print("- Memory: 6.3GB to 6.8GB available")
    print("- Workloads: Sequential, Random, Mixed patterns")
    print()
    
    # Your actual experiment statistics
    REAL_STATS = {
        'initial_faults': 6453748,
        'final_faults': 6942149,
        'fault_increase': 488401,
        'faults_per_second': 1816,  # 488401 / 269
        'memory_range_kb': [6300000, 6800000],
        'major_faults_initial': 15945,
        'major_faults_final': 15965
    }
    
    training_data = {
        'metadata': {
            'description': 'Hybrid AI Page Replacement Training Data - Real Linux VM Experiment',
            'based_on_real_data': True,
            'experiment_stats': REAL_STATS,
            'total_sequences': 1000,
            'data_splits': {'train': 700, 'val': 150, 'test': 150},
            'access_patterns': ['sequential', 'random', 'mixed', 'locality'],
            'input_features': [
                'normalized_page_faults',
                'normalized_major_faults', 
                'memory_pressure',
                'page_access_pattern'
            ],
            'targets': [
                'next_page_faults',
                'next_major_faults',
                'next_memory_pressure',
                'next_pages'
            ]
        },
        'training_set': [],
        'validation_set': [],
        'test_set': []
    }
    
    # Generate sequences for each pattern type
    all_sequences = []
    
    for pattern in training_data['metadata']['access_patterns']:
        print(f"Generating {pattern} sequences...")
        sequences = generate_sequences_for_pattern(pattern, REAL_STATS, 250)
        all_sequences.extend(sequences)
    
    # Shuffle all sequences
    random.shuffle(all_sequences)
    
    # Split into train/validation/test
    total = len(all_sequences)
    train_count = int(0.7 * total)
    val_count = int(0.15 * total)
    
    training_data['training_set'] = all_sequences[:train_count]
    training_data['validation_set'] = all_sequences[train_count:train_count + val_count]
    training_data['test_set'] = all_sequences[train_count + val_count:]
    
    return training_data

def generate_sequences_for_pattern(pattern_type, real_stats, count):
    """Generate training sequences for a specific access pattern"""
    sequences = []
    
    for i in range(count):
        # Determine sequence characteristics based on pattern
        if pattern_type == 'sequential':
            seq_length = random.randint(30, 60)
            fault_variability = 0.1
            page_sequence = generate_sequential_pages(seq_length)
            trust_confidence = 0.85
        elif pattern_type == 'random':
            seq_length = random.randint(20, 40)
            fault_variability = 0.3
            page_sequence = generate_random_pages(seq_length)
            trust_confidence = 0.35
        elif pattern_type == 'mixed':
            seq_length = random.randint(25, 50)
            fault_variability = 0.2
            page_sequence = generate_mixed_pages(seq_length)
            trust_confidence = 0.65
        else:  # locality
            seq_length = random.randint(35, 70)
            fault_variability = 0.15
            page_sequence = generate_locality_pages(seq_length)
            trust_confidence = 0.75
        
        # Generate memory history based on real experiment data
        memory_history = generate_memory_history(seq_length, real_stats, fault_variability)
        
        # Generate targets (what the AI should predict)
        targets = generate_targets(memory_history, page_sequence, pattern_type, real_stats)
        
        # Create the training sequence
        sequence = {
            'sequence_id': f"{pattern_type}_{i}",
            'pattern_type': pattern_type,
            'input_features': {
                'memory_history': memory_history,
                'page_sequence': page_sequence,
                'current_memory_pressure': memory_history[-1]['mem_pressure'] if memory_history else 0.3
            },
            'targets': targets,
            'trust_factors': {
                'pattern_confidence': trust_confidence,
                'memory_stability': random.uniform(0.7, 0.9),
                'historical_accuracy': random.uniform(0.6, 0.8),
                'pressure_sensitivity': random.uniform(0.5, 0.8)
            },
            'metadata': {
                'sequence_length': seq_length,
                'based_on_real_experiment': True
            }
        }
        
        sequences.append(sequence)
    
    return sequences

def generate_sequential_pages(length):
    """Generate sequential page access pattern"""
    start_page = random.randint(0, 900)
    return [start_page + i for i in range(length)]

def generate_random_pages(length):
    """Generate random page access pattern"""
    return [random.randint(0, 1000) for _ in range(length)]

def generate_mixed_pages(length):
    """Generate mixed sequential/random pattern"""
    pages = []
    current_page = random.randint(0, 900)
    
    for i in range(length):
        if random.random() < 0.7:  # 70% sequential
            pages.append(current_page)
            current_page += 1
        else:  # 30% random
            pages.append(random.randint(0, 1000))
    
    return pages

def generate_locality_pages(length):
    """Generate pages with spatial locality"""
    pages = []
    current_locality = random.randint(0, 800)
    
    for i in range(length):
        # Access pages within current locality (256-page window)
        pages.append(current_locality + random.randint(0, 255))
        
        # Occasionally jump to new locality
        if random.random() < 0.02:
            current_locality = random.randint(0, 800)
    
    return pages

def generate_memory_history(length, real_stats, variability):
    """Generate realistic memory history based on actual experiment data"""
    history = []
    
    # Start from a random point in the experiment
    start_faults = real_stats['initial_faults'] + random.randint(0, 200000)
    start_major = real_stats['major_faults_initial'] + random.randint(0, 10)
    
    for step in range(length):
        # Calculate current faults based on real progression
        time_progress = step / length
        current_faults = start_faults + int(step * real_stats['faults_per_second'] * 
                                          random.uniform(1 - variability, 1 + variability))
        
        # Realistic memory available (from your 6.3GB-6.8GB range)
        mem_available = random.randint(*real_stats['memory_range_kb'])
        mem_total = 8388608  # 8GB in KB
        mem_pressure = 1.0 - (mem_available / mem_total)
        
        # Major faults slowly increasing
        major_faults = start_major + int(time_progress * 15)  # Slow increase
        
        history.append({
            'timestep': step,
            'page_faults': current_faults,
            'page_faults_normalized': current_faults / 7000000.0,  # Normalized
            'major_faults': major_faults,
            'major_faults_normalized': major_faults / 16000.0,     # Normalized
            'memory_available': mem_available,
            'mem_pressure': mem_pressure
        })
    
    return history

def generate_targets(memory_history, page_sequence, pattern_type, real_stats):
    """Generate prediction targets for the AI model"""
    if not memory_history:
        return {}
    
    last_memory = memory_history[-1]
    
    # Predict next faults (continue the trend)
    next_faults = last_memory['page_faults'] + int(real_stats['faults_per_second'] * 
                                                  random.uniform(0.8, 1.2))
    
    # Predict next memory state
    next_mem_available = random.randint(*real_stats['memory_range_kb'])
    next_mem_pressure = 1.0 - (next_mem_available / 8388608)
    
    # Predict next pages based on pattern
    next_pages = predict_future_pages(pattern_type, page_sequence)
    
    return {
        'next_page_faults': next_faults,
        'next_page_faults_normalized': next_faults / 7000000.0,
        'next_major_faults': last_memory['major_faults'] + 1,
        'next_major_faults_normalized': (last_memory['major_faults'] + 1) / 16000.0,
        'next_memory_pressure': next_mem_pressure,
        'next_pages': next_pages
    }

def predict_future_pages(pattern_type, current_sequence):
    """Predict the next few pages based on the access pattern"""
    if not current_sequence:
        return []
    
    if pattern_type == 'sequential':
        last_page = current_sequence[-1]
        return [last_page + i + 1 for i in range(5)]
    elif pattern_type == 'random':
        return [random.randint(0, 1000) for _ in range(5)]
    elif pattern_type == 'mixed':
        last_page = current_sequence[-1]
        next_pages = []
        current = last_page
        for i in range(5):
            if random.random() < 0.6:
                next_pages.append(current)
                current += 1
            else:
                next_pages.append(random.randint(0, 1000))
        return next_pages
    else:  # locality
        last_page = current_sequence[-1]
        base_locality = last_page - (last_page % 256)
        return [base_locality + random.randint(0, 255) for _ in range(5)]

def main():
    print("Creating AI training data for Hybrid Page Replacement System...")
    print("No external packages required - using only Python standard library")
    print()
    
    # Generate the complete training dataset
    training_data = generate_training_data_based_on_real_experiment()
    
    # Save to file
    output_file = "HYBRID_AI_TRAINING_DATA.json"
    with open(output_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print("✅ SUCCESS! Training data created successfully!")
    print()
    print("📊 DATASET SUMMARY:")
    print(f"   Total sequences: {len(training_data['training_set']) + len(training_data['validation_set']) + len(training_data['test_set'])}")
    print(f"   Training set: {len(training_data['training_set'])} sequences")
    print(f"   Validation set: {len(training_data['validation_set'])} sequences")
    print(f"   Test set: {len(training_data['test_set'])} sequences")
    print()
    
    # Show pattern distribution
    pattern_counts = {}
    for seq in training_data['training_set']:
        pattern = seq['pattern_type']
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    print("🔢 PATTERN DISTRIBUTION:")
    for pattern in sorted(pattern_counts.keys()):
        count = pattern_counts[pattern]
        print(f"   {pattern:12}: {count:3} sequences")
    
    print()
    print("🎯 BASED ON YOUR REAL LINUX VM EXPERIMENT:")
    print(f"   - Page faults: {training_data['metadata']['experiment_stats']['initial_faults']:,} to {training_data['metadata']['experiment_stats']['final_faults']:,}")
    print(f"   - Total increase: {training_data['metadata']['experiment_stats']['fault_increase']:,} faults")
    print(f"   - Duration: 269 seconds")
    print(f"   - Fault rate: ~{training_data['metadata']['experiment_stats']['faults_per_second']:,.0f} faults/second")
    print()
    print("💾 Saved to: HYBRID_AI_TRAINING_DATA.json")
    print()
    print("🚀 Ready for your AI model training!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import random

def demonstrate_training_data_usage():
    """Show how to use the generated training data"""
    
    print("=== HOW TO USE YOUR HYBRID AI TRAINING DATA ===")
    print()
    
    # Load the data
    try:
        with open('HYBRID_AI_TRAINING_DATA.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: Training data file not found!")
        return
    
    print("✅ Data loaded successfully!")
    print()
    
    # Show dataset info
    metadata = data['metadata']
    print("📊 DATASET INFORMATION:")
    print(f"   Description: {metadata['description']}")
    print(f"   Based on real experiment: {metadata['based_on_real_data']}")
    print(f"   Total sequences: {len(data['training_set']) + len(data['validation_set']) + len(data['test_set'])}")
    print(f"   Access patterns: {', '.join(metadata['access_patterns'])}")
    print()
    
    # Show real experiment stats
    stats = metadata['experiment_stats']
    print("🎯 REAL EXPERIMENT STATISTICS:")
    print(f"   Initial faults: {stats['initial_faults']:,}")
    print(f"   Final faults: {stats['final_faults']:,}")
    print(f"   Fault increase: {stats['fault_increase']:,}")
    print(f"   Faults per second: {stats['faults_per_second']:,.0f}")
    print()
    
    # Demonstrate accessing training data
    print("🔧 HOW TO ACCESS TRAINING DATA:")
    print()
    print("1. Access different datasets:")
    print("   training_sequences = data['training_set']")
    print("   validation_sequences = data['validation_set']")
    print("   test_sequences = data['test_set']")
    print()
    
    # Show a sample sequence
    if data['training_set']:
        sample = data['training_set'][0]
        print("2. SAMPLE SEQUENCE STRUCTURE:")
        print(f"   Pattern type: {sample['pattern_type']}")
        print(f"   Sequence ID: {sample['sequence_id']}")
        print()
        
        print("3. INPUT FEATURES:")
        inputs = sample['input_features']
        print(f"   Memory history: {len(inputs['memory_history'])} timesteps")
        print(f"   Each timestep has: {list(inputs['memory_history'][0].keys())}")
        print(f"   Page sequence: {len(inputs['page_sequence'])} pages")
        print(f"   Current memory pressure: {inputs['current_memory_pressure']:.3f}")
        print()
        
        print("4. TARGETS (what to predict):")
        targets = sample['targets']
        for key, value in targets.items():
            if 'normalized' in key:
                print(f"   {key}: {value:.4f}")
            elif key == 'next_pages':
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        print()
        
        print("5. TRUST FACTORS (for hybrid system):")
        trust = sample['trust_factors']
        for key, value in trust.items():
            print(f"   {key}: {value:.2f}")
        print()
    
    print("🚀 EXAMPLE USAGE IN YOUR AI SYSTEM:")
    print("""
# Pseudocode for your Hybrid AI Page Replacement

def train_ai_model(training_sequences):
    for sequence in training_sequences:
        # Extract features
        memory_history = sequence['input_features']['memory_history']
        page_sequence = sequence['input_features']['page_sequence']
        trust_factors = sequence['trust_factors']
        
        # Format for GRU/LSTM
        X_memory = [[step['page_faults_normalized'], 
                     step['major_faults_normalized'],
                     step['mem_pressure']] for step in memory_history]
        
        X_pages = page_sequence
        
        # Targets
        y_next_faults = sequence['targets']['next_page_faults_normalized']
        y_next_pages = sequence['targets']['next_pages']
        
        # Train your model here...
        # model.train(X_memory, X_pages, y_next_faults, y_next_pages)

def hybrid_page_replacement(current_state, ai_prediction, trust_factors):
    \"\"\"Your hybrid system combining AI and LRU\"\"\"\"
    trust_score = (trust_factors['pattern_confidence'] * 0.4 +
                   trust_factors['memory_stability'] * 0.3 +
                   trust_factors['historical_accuracy'] * 0.3)
    
    if trust_score > 0.6:  # Your threshold
        return use_ai_prediction(ai_prediction)
    else:
        return use_lru_fallback()
    """)

if __name__ == "__main__":
    demonstrate_training_data_usage()

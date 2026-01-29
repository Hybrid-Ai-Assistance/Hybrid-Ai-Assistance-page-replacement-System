#!/usr/bin/env python3
import json
import numpy as np

def create_model_ready_data():
    """Format the data for your Hybrid AI page replacement system"""
    
    try:
        with open('real_experiment_training_data.json', 'r') as f:
            training_data = json.load(f)
    except FileNotFoundError:
        print("Training data not found. Please run the previous script first.")
        return
    
    print("Formatting data for GRU/LSTM model training...")
    
    model_ready_data = {
        'metadata': {
            'description': 'Hybrid AI Page Replacement Training Data',
            'source': 'Real Linux VM Experiment',
            'total_sequences': len(training_data),
            'input_features': ['normalized_faults', 'normalized_major_faults', 'memory_pressure'],
            'targets': ['next_faults', 'next_major_faults', 'next_pages'],
            'based_on_real_data': True
        },
        'training_set': [],
        'validation_set': [],
        'test_set': []
    }
    
    # Normalization factors based on your real data
    max_faults = 7000000  # Slightly above your max of 6,942,149
    max_major_faults = 16000  # Slightly above your max of 15,965
    
    # Split data
    total = len(training_data)
    train_size = int(0.7 * total)
    val_size = int(0.15 * total)
    
    for i, seq in enumerate(training_data):
        # Format inputs for your AI model
        formatted_seq = {
            'id': seq['sequence_id'],
            'pattern_type': seq['pattern_type'],
            
            # Memory history features (for GRU/LSTM)
            'X_memory': [],
            
            # Page access sequence (for pattern recognition)
            'X_pages': seq['page_access_pattern'],
            
            # Targets
            'y_next_faults': seq['targets']['next_page_faults'] / max_faults,
            'y_next_major_faults': seq['targets']['next_major_faults'] / max_major_faults,
            'y_next_pages': seq['targets']['next_pages'],
            'y_next_pressure': seq['targets']['next_memory_pressure'],
            
            # For your hybrid trust system
            'trust_factors': seq['trust_factors'],
            
            # Raw values for reference
            'raw_target_faults': seq['targets']['next_page_faults']
        }
        
        # Format memory history with normalized values
        for mem_step in seq['memory_history']:
            normalized_step = [
                mem_step['pgfault'] / max_faults,
                mem_step['pgmajfault'] / max_major_faults, 
                mem_step['mem_pressure']
            ]
            formatted_seq['X_memory'].append(normalized_step)
        
        # Add to appropriate set
        if i < train_size:
            model_ready_data['training_set'].append(formatted_seq)
        elif i < train_size + val_size:
            model_ready_data['validation_set'].append(formatted_seq)
        else:
            model_ready_data['test_set'].append(formatted_seq)
    
    return model_ready_data

def main():
    print("=== CREATING FINAL MODEL-READY DATA ===")
    
    model_data = create_model_ready_data()
    
    if not model_data['training_set']:
        print("No data to process!")
        return
    
    # Save the final model-ready data
    output_file = "FINAL_hybrid_ai_model_data.json"
    with open(output_file, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    print(f"✓ Training sequences: {len(model_data['training_set'])}")
    print(f"✓ Validation sequences: {len(model_data['validation_set'])}")
    print(f"✓ Test sequences: {len(model_data['test_set'])}")
    print(f"✓ Saved to: {output_file}")
    
    # Show sample
    sample = model_data['training_set'][0]
    print(f"\n=== SAMPLE MODEL INPUT ===")
    print(f"Pattern: {sample['pattern_type']}")
    print(f"Memory sequence: {len(sample['X_memory'])} steps × {len(sample['X_memory'][0])} features")
    print(f"Page sequence: {len(sample['X_pages'])} pages")
    print(f"Target - Next faults (normalized): {sample['y_next_faults']:.4f}")
    print(f"Trust - Pattern confidence: {sample['trust_factors']['pattern_confidence']:.2f}")

if __name__ == "__main__":
    main()

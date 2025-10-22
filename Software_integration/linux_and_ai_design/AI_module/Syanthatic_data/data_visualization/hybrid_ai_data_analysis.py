# hybrid_ai_data_analysis.py
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class HybridAIDataAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.df_sequences = None
        self.load_data()
    
    def load_data(self):
        """JSON data load karta hai"""
        try:
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
            print("✅ Data loaded successfully!")
            print(f"Training sequences: {len(self.data['training_set'])}")
            print(f"Validation sequences: {len(self.data['validation_set'])}")
            print(f"Test sequences: {len(self.data['test_set'])}")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
    def create_sequences_dataframe(self):
        """Sequences ko pandas DataFrame mein convert karta hai"""
        sequences_data = []
        
        for seq in self.data['training_set']:
            seq_info = {
                'sequence_id': seq.get('sequence_id'),
                'pattern_type': seq.get('pattern_type'),
                'memory_history_length': len(seq.get('input_features', {}).get('memory_history', [])),
                'page_sequence_length': len(seq.get('input_features', {}).get('page_sequence', [])),
                'current_memory_pressure': seq.get('input_features', {}).get('current_memory_pressure', 0),
                'next_page_faults': seq.get('targets', {}).get('next_page_faults', 0),
                'next_page_faults_normalized': seq.get('targets', {}).get('next_page_faults_normalized', 0),
                'pattern_confidence': seq.get('trust_factors', {}).get('pattern_confidence', 0),
                'memory_stability': seq.get('trust_factors', {}).get('memory_stability', 0),
                'historical_accuracy': seq.get('trust_factors', {}).get('historical_accuracy', 0)
            }
            sequences_data.append(seq_info)
        
        self.df_sequences = pd.DataFrame(sequences_data)
        return self.df_sequences
    
    def analyze_patterns(self):
        """Different patterns ka analysis karta hai"""
        if self.df_sequences is None:
            self.create_sequences_dataframe()
        
        print("🎯 PATTERN ANALYSIS:")
        print(self.df_sequences['pattern_type'].value_counts())
        
        # Pattern-wise statistics
        pattern_stats = self.df_sequences.groupby('pattern_type').agg({
            'memory_history_length': ['mean', 'std'],
            'pattern_confidence': ['mean', 'std'],
            'next_page_faults': ['mean', 'std']
        }).round(3)
        
        return pattern_stats
    
    def plot_pattern_distribution(self):
        """Pattern distribution plot karta hai"""
        plt.figure(figsize=(10, 6))
        pattern_counts = self.df_sequences['pattern_type'].value_counts()
        
        plt.subplot(1, 2, 1)
        pattern_counts.plot(kind='bar', color='skyblue')
        plt.title('Pattern Type Distribution')
        plt.xlabel('Pattern Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        
        plt.subplot(1, 2, 2)
        plt.pie(pattern_counts.values, labels=pattern_counts.index, autopct='%1.1f%%')
        plt.title('Pattern Distribution')
        
        plt.tight_layout()
        plt.show()
    
    def analyze_memory_pressure(self):
        """Memory pressure analysis karta hai"""
        pressure_stats = self.df_sequences['current_memory_pressure'].describe()
        
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 3, 1)
        plt.hist(self.df_sequences['current_memory_pressure'], bins=20, alpha=0.7, color='orange')
        plt.title('Memory Pressure Distribution')
        plt.xlabel('Memory Pressure')
        plt.ylabel('Frequency')
        
        plt.subplot(1, 3, 2)
        self.df_sequences.boxplot(column='current_memory_pressure', by='pattern_type')
        plt.title('Memory Pressure by Pattern')
        plt.suptitle('')  # Remove automatic title
        plt.xticks(rotation=45)
        
        plt.subplot(1, 3, 3)
        pressure_by_pattern = self.df_sequences.groupby('pattern_type')['current_memory_pressure'].mean()
        pressure_by_pattern.plot(kind='bar', color='lightgreen')
        plt.title('Avg Memory Pressure by Pattern')
        plt.xlabel('Pattern Type')
        plt.ylabel('Average Pressure')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.show()
        
        return pressure_stats
    
    def analyze_trust_factors(self):
        """Trust factors ka analysis karta hai"""
        trust_stats = self.df_sequences[['pattern_confidence', 'memory_stability', 'historical_accuracy']].describe()
        
        plt.figure(figsize=(15, 4))
        
        # Trust factors distribution
        plt.subplot(1, 3, 1)
        plt.hist(self.df_sequences['pattern_confidence'], bins=20, alpha=0.7, color='red', label='Pattern Confidence')
        plt.hist(self.df_sequences['memory_stability'], bins=20, alpha=0.7, color='blue', label='Memory Stability')
        plt.hist(self.df_sequences['historical_accuracy'], bins=20, alpha=0.7, color='green', label='Historical Accuracy')
        plt.title('Trust Factors Distribution')
        plt.xlabel('Trust Score')
        plt.ylabel('Frequency')
        plt.legend()
        
        # Correlation heatmap
        plt.subplot(1, 3, 2)
        correlation = self.df_sequences[['pattern_confidence', 'memory_stability', 'historical_accuracy', 'current_memory_pressure']].corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
        plt.title('Trust Factors Correlation')
        
        # Pattern-wise trust scores
        plt.subplot(1, 3, 3)
        pattern_trust = self.df_sequences.groupby('pattern_type')[['pattern_confidence', 'memory_stability', 'historical_accuracy']].mean()
        pattern_trust.plot(kind='bar', ax=plt.gca())
        plt.title('Average Trust Scores by Pattern')
        plt.xlabel('Pattern Type')
        plt.ylabel('Average Trust Score')
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.show()
        
        return trust_stats
    
    def show_sample_sequence(self, sequence_index=0):
        """Sample sequence ko detail mein dikhata hai"""
        if sequence_index >= len(self.data['training_set']):
            print("❌ Sequence index out of range!")
            return
        
        seq = self.data['training_set'][sequence_index]
        
        print(f"🔍 DETAILED VIEW - Sequence {sequence_index}:")
        print(f"ID: {seq.get('sequence_id')}")
        print(f"Pattern Type: {seq.get('pattern_type')}")
        print()
        
        # Input features
        inputs = seq.get('input_features', {})
        print("📥 INPUT FEATURES:")
        print(f"  Memory History Steps: {len(inputs.get('memory_history', []))}")
        print(f"  Page Sequence Length: {len(inputs.get('page_sequence', []))}")
        print(f"  Current Memory Pressure: {inputs.get('current_memory_pressure', 0):.3f}")
        print()
        
        # Memory history preview
        memory_history = inputs.get('memory_history', [])
        if memory_history:
            print("📊 MEMORY HISTORY (First 5 steps):")
            for i, step in enumerate(memory_history[:5]):
                print(f"  Step {i}: Faults={step.get('page_faults', 0):,}, "
                      f"Pressure={step.get('mem_pressure', 0):.3f}, "
                      f"Major Faults={step.get('major_faults', 0)}")
            print()
        
        # Page sequence preview
        pages = inputs.get('page_sequence', [])
        print(f"📄 PAGE SEQUENCE (First 10 pages): {pages[:10]}")
        print()
        
        # Targets
        targets = seq.get('targets', {})
        print("🎯 TARGETS (AI Prediction):")
        for key, value in targets.items():
            if isinstance(value, list):
                print(f"  {key}: {value[:3]}...")  # First 3 elements
            else:
                print(f"  {key}: {value}")
        print()
        
        # Trust factors
        trust = seq.get('trust_factors', {})
        print("🤝 TRUST FACTORS:")
        for key, value in trust.items():
            print(f"  {key}: {value:.3f}")

# Usage example:
if __name__ == "__main__":
    # File path adjust karo according to tumhara system
    analyzer = HybridAIDataAnalyzer('FINAL_hybrid_ai_model_data.json')
    
    # Data analysis
    df_sequences = analyzer.create_sequences_dataframe()
    pattern_stats = analyzer.analyze_patterns()
    
    # Visualizations
    analyzer.plot_pattern_distribution()
    analyzer.analyze_memory_pressure()
    analyzer.analyze_trust_factors()
    
    # Sample sequence
    analyzer.show_sample_sequence(0)
    
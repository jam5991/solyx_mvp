import numpy as np
import pandas as pd
from pathlib import Path

def generate_fake_training_data():
    """Generate fake training data for testing"""
    # Create sample data (e.g., fake image classification dataset)
    n_samples = 1000
    
    # Features: fake image data (28x28 pixels)
    X = np.random.rand(n_samples, 28, 28)
    # Labels: 10 classes (0-9)
    y = np.random.randint(0, 10, n_samples)
    
    # Save to numpy files
    data_dir = Path(__file__).parent / "fake_dataset"
    data_dir.mkdir(exist_ok=True)
    
    np.save(data_dir / "X_train.npy", X)
    np.save(data_dir / "y_train.npy", y)
    
    # Create metadata
    metadata = pd.DataFrame({
        'num_samples': [n_samples],
        'input_shape': ['28x28'],
        'num_classes': [10],
        'created_at': [pd.Timestamp.now()]
    })
    metadata.to_csv(data_dir / "metadata.csv", index=False)
    
    return data_dir

if __name__ == "__main__":
    data_dir = generate_fake_training_data()
    print(f"Generated fake dataset at: {data_dir}") 
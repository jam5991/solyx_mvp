import asyncio
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from drm_core import DRMCore
from drm_core.config.settings import DRMConfig


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
    data_dir.mkdir(exist_ok=True)  # This ensures the directory exists

    # These will overwrite existing files
    np.save(data_dir / "X_train.npy", X)
    np.save(data_dir / "y_train.npy", y)

    # This will overwrite the existing metadata.csv
    metadata = pd.DataFrame(
        {
            "num_samples": [n_samples],
            "input_shape": ["28x28"],
            "num_classes": [10],
            "created_at": [pd.Timestamp.now()],  # New timestamp
        }
    )
    metadata.to_csv(data_dir / "metadata.csv", index=False)

    return data_dir


def train_model(epochs=5, batch_size=32, learning_rate=0.001, **kwargs):
    """Training function that DRM will execute"""
    # Load the fake data
    data_dir = Path(__file__).parent / "fake_dataset"
    X = torch.FloatTensor(np.load(data_dir / "X_train.npy"))
    y = torch.LongTensor(np.load(data_dir / "y_train.npy"))

    # Define a simple CNN model
    model = nn.Sequential(
        nn.Flatten(), nn.Linear(28 * 28, 128), nn.ReLU(), nn.Linear(128, 10)
    )

    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    for epoch in range(epochs):
        total_loss = 0
        for i in range(0, len(X), batch_size):
            batch_X = X[i : i + batch_size]
            batch_y = y[i : i + batch_size]

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / (len(X) / batch_size)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

    # Calculate final accuracy
    with torch.no_grad():
        outputs = model(X)
        _, predicted = torch.max(outputs.data, 1)
        accuracy = (predicted == y).sum().item() / len(y)

    return {
        "final_accuracy": accuracy,
        "final_loss": avg_loss,
        "epochs_completed": epochs,
    }


async def submit_training_job():
    # Initialize DRM
    config = DRMConfig()
    drm = DRMCore(config)
    await drm.initialize()

    # Create job specification
    job_spec = {
        "job_id": "test_training_job_001",
        "workload": {
            "script": "data.generate_fake_data",  # Python path to your module
            "function": "train_model",  # Function to execute
            "epochs": 5,
            "batch_size": 32,
            "learning_rate": 0.001,
        },
        "min_memory": 8,  # Minimum GPU memory in GB
        "max_price": 2.0,  # Maximum price per hour willing to pay
        "gpu_type": None,  # Any GPU type is fine
    }

    # Submit the job
    result = await drm.submit_job(job_spec)
    print(f"Job submission result: {result}")

    # Monitor job status
    while True:
        status = drm.get_job_status(job_spec["job_id"])
        print(f"Job status: {status}")
        if status and status["status"] == "completed":
            break
        await asyncio.sleep(5)


if __name__ == "__main__":
    # Generate the dataset first
    data_dir = generate_fake_training_data()
    print(f"Generated fake dataset at: {data_dir}")

    # Submit and monitor the training job
    asyncio.run(submit_training_job())

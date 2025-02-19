import asyncio
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from drm_core import DRMCore
from drm_core.config.settings import DRMConfig

logger = logging.getLogger(__name__)


def generate_fake_training_data() -> Path:
    """Generate a fake dataset for testing the training pipeline"""
    logger.info("Generating fake MNIST-like dataset...")

    np.random.seed(42)

    n_samples = 1000
    n_classes = 10
    img_size = 28

    X = np.zeros((n_samples, img_size, img_size))
    y = np.zeros(n_samples, dtype=np.int64)

    for i in range(n_samples):
        class_idx = i % n_classes
        y[i] = class_idx

        # Base pattern
        if class_idx == 0:  # Horizontal lines with varying spacing
            spacing = np.random.randint(2, 5)
            X[i, ::spacing, :] = 1.0
        elif class_idx == 1:  # Vertical lines with varying spacing
            spacing = np.random.randint(2, 5)
            X[i, :, ::spacing] = 1.0
        elif class_idx == 2:  # Diagonal lines with varying thickness
            thickness = np.random.randint(1, 4)
            for t in range(thickness):
                # Create diagonal line with offset
                for j in range(img_size):
                    if j + t < img_size:
                        X[i, j, j + t] = 1.0
        elif class_idx == 3:  # Circles with varying radius
            center = img_size // 2
            radius = np.random.randint(img_size // 6, img_size // 3)
            y_idx, x_idx = np.ogrid[
                -center : img_size - center, -center : img_size - center
            ]
            mask = x_idx * x_idx + y_idx * y_idx <= radius * radius
            X[i][mask] = 1.0
        elif class_idx == 4:  # Squares with varying size
            margin = np.random.randint(img_size // 5, img_size // 3)
            X[i, margin:-margin, margin:-margin] = 1.0
        elif class_idx == 5:  # Cross with varying thickness
            thickness = np.random.randint(1, 4)
            mid = img_size // 2
            X[i, :, mid - thickness : mid + thickness] = 1.0
            X[i, mid - thickness : mid + thickness, :] = 1.0
        elif class_idx == 6:  # Triangle with varying slope
            slope = np.random.uniform(0.5, 1.5)
            for j in range(img_size):
                width = int(max(1, j * slope))
                X[i, j, max(0, j - width) : min(img_size, j + width)] = 1.0
        elif class_idx == 7:  # Checkerboard with varying size
            size = np.random.randint(2, 5)
            X[i, ::size, ::size] = 1.0
        elif class_idx == 8:  # Border with varying thickness
            thickness = np.random.randint(1, 4)
            X[i, :thickness, :] = X[i, -thickness:, :] = 1.0
            X[i, :, :thickness] = X[i, :, -thickness:] = 1.0
        elif class_idx == 9:  # Dots with varying density
            spacing = np.random.randint(3, 6)
            X[i, ::spacing, ::spacing] = 1.0

        # Add more significant noise
        X[i] += np.random.normal(0, 0.2, (img_size, img_size))

    # Clip values to [0, 1]
    X = np.clip(X, 0, 1)

    # Create output directory and save
    output_dir = Path(__file__).parent / "fake_dataset"
    output_dir.mkdir(exist_ok=True)
    np.save(output_dir / "X_train.npy", X)
    np.save(output_dir / "y_train.npy", y)

    logger.info(f"Generated dataset with {n_samples} samples")
    logger.info(f"X shape: {X.shape}, y shape: {y.shape}")
    logger.info(f"Classes: {np.unique(y)}")
    logger.info(f"Class distribution: {np.bincount(y)}")

    return output_dir


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

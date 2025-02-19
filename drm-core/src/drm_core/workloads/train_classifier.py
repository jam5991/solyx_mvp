import logging
from pathlib import Path

import numpy as np
import ray
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SimpleConvNet(nn.Module):
    """Simple CNN for image classification"""

    def __init__(self):
        super().__init__()
        # Simpler architecture to start
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(16 * 14 * 14, 64)
        self.fc2 = nn.Linear(64, 10)

    def forward(self, x):
        # Add debug prints
        x = self.conv1(x)
        x = F.relu(x)
        x = self.pool(x)

        # Print shape before flatten
        batch_size = x.shape[0]
        x = x.view(batch_size, -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


@ray.remote
class RayTrainer:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - RayTrainer - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        self.model = SimpleConvNet()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.01)

    def train(self, X, y, epochs, batch_size):
        self.logger.info(
            f"Starting training: {epochs} epochs, batch_size {batch_size}"
        )
        self.logger.info(
            f"Dataset: {len(X)} samples, {len(np.unique(y))} classes"
        )

        X = torch.FloatTensor(X).unsqueeze(1)  # Add channel dimension
        y = torch.LongTensor(y)

        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        best_accuracy = 0.0
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            correct = 0
            total = 0

            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += batch_y.size(0)
                correct += (predicted == batch_y).sum().item()

            epoch_loss = total_loss / len(dataloader)
            epoch_accuracy = 100 * correct / total

            self.logger.info(
                f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Accuracy: {epoch_accuracy:.2f}%"
            )

            if epoch_accuracy > best_accuracy:
                best_accuracy = epoch_accuracy

        return {
            "final_accuracy": best_accuracy / 100,
            "final_loss": epoch_loss,
        }


def train_model(data_dir: str, epochs: int = 5, batch_size: int = 32):
    """Train a simple CNN on the fake dataset using Ray"""
    # Configure logging for the Ray worker
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info(
        f"Starting training with {epochs} epochs and batch size {batch_size}"
    )

    # Convert string path to Path object
    data_dir = Path(data_dir)
    logger.info(f"Loading data from {data_dir}")

    try:
        # Load data
        X = np.load(data_dir / "X_train.npy")
        y = np.load(data_dir / "y_train.npy")
        logger.info(f"Data loaded: X shape: {X.shape}, y shape: {y.shape}")

        # Initialize Ray trainer
        trainer = RayTrainer.remote()

        # Launch training job
        logger.info("Launching Ray training job...")
        training_future = trainer.train.remote(X, y, epochs, batch_size)

        # Monitor training progress
        logger.info("Monitoring training progress...")
        result = ray.get(training_future)

        logger.info(
            f"Training completed! Final accuracy: {result['final_accuracy']:.4f}"
        )
        return result

    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        raise

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SimpleConvNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 13 * 13, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = x.view(-1, 32 * 13 * 13)
        x = self.fc1(x)
        return x


@torch.no_grad()
def evaluate(model, X_test, y_test):
    model.eval()
    outputs = model(X_test)
    _, predicted = torch.max(outputs.data, 1)
    accuracy = (predicted == y_test).sum().item() / y_test.size(0)
    return accuracy


def train_model(data_dir: Path, epochs: int = 5, batch_size: int = 32):
    """Train a simple CNN on the fake dataset"""
    print(
        f"Starting training with {epochs} epochs and batch size {batch_size}"
    )
    logger.info(f"Loading data from {data_dir}")
    X = np.load(data_dir / "X_train.npy")
    y = np.load(data_dir / "y_train.npy")

    # Convert to torch tensors
    X = torch.FloatTensor(X).unsqueeze(1)  # Add channel dimension
    y = torch.LongTensor(y)

    print(f"Data loaded: X shape: {X.shape}, y shape: {y.shape}")

    # Create model and optimizer
    model = SimpleConvNet()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    print(
        f"Starting training for {epochs} epochs with batch size {batch_size}"
    )
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        # Training loop
        for i in range(0, len(X), batch_size):
            batch_X = X[i : i + batch_size]
            batch_y = y[i : i + batch_size]

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            if i % (5 * batch_size) == 0:  # Log every 5 batches
                print(
                    f"Epoch {epoch+1}/{epochs} - Batch {i}/{len(X)} - Loss: {loss.item():.4f}"
                )

        # Evaluate
        accuracy = evaluate(model, X, y)
        print(
            f"Epoch {epoch+1}/{epochs} - Average Loss: {total_loss/len(X):.4f} - Accuracy: {accuracy:.4f}"
        )

    print("Training completed!")
    return model

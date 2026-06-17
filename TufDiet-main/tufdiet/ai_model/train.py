import os
import json
import argparse
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms


class Food101Dataset(Dataset):
    def __init__(self, data_dir, split='train', transform=None):
        self.data_dir = data_dir
        self.split = split
        self.transform = transform
        self.classes = self._load_classes()
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.images = self._load_image_paths()

    def _load_classes(self):
        return [
            'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
            'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
            'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
            'ceviche', 'cheesecake', 'chicken_curry', 'chicken_quesadilla', 'chicken_wings',
            'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder', 'club_sandwich',
            'crab_cakes', 'creme_brulee', 'croissant', 'cup_cakes', 'deviled_eggs',
            'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots',
            'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries',
            'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt',
            'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon',
            'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog',
            'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna', 'lobster_bisque',
            'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels',
            'nachos', 'omelette', 'onion_rings', 'oysters', 'pad_thai',
            'paella', 'pancakes', 'panna_cotta', 'peking_duck', 'pho',
            'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich',
            'ramen', 'ravioli', 'red_velvet_cake', 'risotto', 'samosa',
            'sashimi', 'scallops', 'seaweed_salad', 'spaghetti_bolognese', 'spaghetti_carbonara',
            'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos',
            'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
        ]

    def _load_image_paths(self):
        images = []
        split_file = os.path.join(self.data_dir, 'meta', f'{self.split}.txt')
        if os.path.exists(split_file):
            with open(split_file, 'r') as f:
                for line in f:
                    parts = line.strip().split('/')
                    if len(parts) < 2:
                        continue
                    class_name = parts[0]
                    img_name = parts[1]
                    img_path = os.path.join(self.data_dir, 'images', class_name, f'{img_name}.jpg')
                    if os.path.exists(img_path) and class_name in self.class_to_idx:
                        images.append((img_path, self.class_to_idx[class_name]))
        print(f"Loaded {len(images)} images for {self.split} split")
        return images

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path, label = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label


class FoodClassifierTrainer:
    def __init__(self, data_dir, output_dir, batch_size=32, num_epochs=30, learning_rate=0.001):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.optimizer = None
        self.criterion = None
        self.scheduler = None
        self.train_transform = self._get_train_transform()
        self.val_transform = self._get_val_transform()
        self.classes = self._load_classes()

    def _load_classes(self):
        return [
            'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
            'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
            'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
            'ceviche', 'cheesecake', 'chicken_curry', 'chicken_quesadilla', 'chicken_wings',
            'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder', 'club_sandwich',
            'crab_cakes', 'creme_brulee', 'croissant', 'cup_cakes', 'deviled_eggs',
            'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots',
            'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries',
            'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt',
            'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon',
            'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog',
            'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna', 'lobster_bisque',
            'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels',
            'nachos', 'omelette', 'onion_rings', 'oysters', 'pad_thai',
            'paella', 'pancakes', 'panna_cotta', 'peking_duck', 'pho',
            'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich',
            'ramen', 'ravioli', 'red_velvet_cake', 'risotto', 'samosa',
            'sashimi', 'scallops', 'seaweed_salad', 'spaghetti_bolognese', 'spaghetti_carbonara',
            'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos',
            'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
        ]

    def _get_train_transform(self):
        return transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.RandomRotation(degrees=15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _get_val_transform(self):
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def prepare_data(self):
        train_dataset = Food101Dataset(self.data_dir, split='train', transform=self.train_transform)
        val_dataset = Food101Dataset(self.data_dir, split='test', transform=self.val_transform)
        self.train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=4, pin_memory=True)
        self.val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=4, pin_memory=True)
        print(f'Training samples: {len(train_dataset)}, Validation samples: {len(val_dataset)}')

    def build_model(self):
        self.model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        num_features = self.model.classifier[1].in_features
        self.model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(num_features, len(self.classes))
        )
        self.model = self.model.to(self.device)

    def setup_training(self):
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=self.num_epochs, eta_min=1e-6)

    def train_epoch(self):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        progress_bar = tqdm(self.train_loader, desc='Training')

        for images, labels in progress_bar:
            images = images.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100 * correct / total:.2f}%'
            })

        return running_loss / len(self.train_loader), 100 * correct / total

    def validate(self):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in tqdm(self.val_loader, desc='Validating'):
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        return running_loss / len(self.val_loader), 100 * correct / total

    def save_checkpoint(self, epoch, train_loss, train_acc, val_loss, val_acc, best_val_acc):
        os.makedirs(self.output_dir, exist_ok=True)
        checkpoint_path = os.path.join(self.output_dir, 'checkpoint.pth')
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'train_loss': train_loss,
            'train_acc': train_acc,
            'val_loss': val_loss,
            'val_acc': val_acc,
            'best_val_acc': best_val_acc,
            'classes': self.classes,
        }, checkpoint_path)
        print(f'Checkpoint saved at epoch {epoch}')

    def save_model(self, epoch, train_loss, train_acc, val_loss, val_acc):
        os.makedirs(self.output_dir, exist_ok=True)
        model_path = os.path.join(self.output_dir, 'food_classifier.pth')
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_loss': train_loss,
            'train_acc': train_acc,
            'val_loss': val_loss,
            'val_acc': val_acc,
            'classes': self.classes,
        }, model_path)

        classes_path = os.path.join(self.output_dir, 'food_classes.txt')
        with open(classes_path, 'w') as f:
            f.write('\n'.join(self.classes))

        print(f'Best model saved to {model_path}')

    def load_checkpoint(self):
        checkpoint_path = os.path.join(self.output_dir, 'checkpoint.pth')
        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            start_epoch = checkpoint['epoch']
            best_val_acc = checkpoint.get('best_val_acc', 0.0)
            print(f'Checkpoint loaded: resuming from epoch {start_epoch}')
            return start_epoch, best_val_acc
        return 0, 0.0

    def train(self, resume=False):
        print(f'Using device: {self.device}')
        print(f'Training for {self.num_epochs} epochs')
        best_val_acc = 0.0
        start_epoch = 0

        if resume:
            start_epoch, best_val_acc = self.load_checkpoint()

        for epoch in range(start_epoch + 1, self.num_epochs + 1):
            print(f'\nEpoch {epoch}/{self.num_epochs}')
            print('-' * 50)

            train_loss, train_acc = self.train_epoch()
            val_loss, val_acc = self.validate()

            self.scheduler.step()

            print(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
            print(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')
            print(f'Learning Rate: {self.scheduler.get_last_lr()[0]:.6f}')

            self.save_checkpoint(epoch, train_loss, train_acc, val_loss, val_acc, best_val_acc)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model(epoch, train_loss, train_acc, val_loss, val_acc)

        print(f'\nTraining completed. Best validation accuracy: {best_val_acc:.2f}%')
        return best_val_acc


def main():
    parser = argparse.ArgumentParser(description='Train Food-101 Classification Model')
    parser.add_argument('--data_dir', type=str, default='./data/food-101', help='Path to Food-101 dataset')
    parser.add_argument('--output_dir', type=str, default='./output', help='Path to save trained model')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    parser.add_argument('--num_epochs', type=int, default=30, help='Number of training epochs')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Initial learning rate')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')

    args = parser.parse_args()

    trainer = FoodClassifierTrainer(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate
    )

    trainer.prepare_data()
    trainer.build_model()
    trainer.setup_training()
    trainer.train(resume=args.resume)


if __name__ == '__main__':
    main()

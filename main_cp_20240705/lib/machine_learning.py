import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image


class MachineLearning:
    """Class for machine learning operations."""

    def __init__(self, model_path: str, model_type: str) -> None:
        """
        Initializes the model and loads the state dict.

        Args:
            model_path (str): Path to the model state dictionary.
            model_type (str): Type of the model to be used.
        """
        if model_type == "vgg19_bn":
            self.model = models.vgg19_bn(pretrained=False)
            self.model.classifier[6] = torch.nn.Linear(
                in_features=4096, out_features=16
            )
            state_dict = torch.load(model_path, map_location=torch.device("cpu"))
            self.model.load_state_dict(state_dict)
        else:
            self.model = None

        if self.model:
            self.model.eval()
            self.transform = transforms.Compose(
                [
                    transforms.Resize((224, 224)),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=0.5, std=0.5),
                ]
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def inference(self, image_path: str) -> int:
        """
        Performs inference on an image.

        Args:
            image_path (str): Path to the input image.

        Returns:
            int: Predicted class index.
        """
        image = Image.open(image_path)
        image_tensor = self.transform(image)
        image_tensor = image_tensor.unsqueeze(0)
        output = self.model(image_tensor)
        print(output)
        predicted_class = torch.argmax(output, dim=1).item()

        # テンソルの値を降順にソートし、そのインデックスを取得
        sorted_output, indices = torch.sort(output, descending=True)

        largest_value = sorted_output[0].item()
        second_largest_value = sorted_output[1].item()
        if largest_value - second_largest_value < 2:
            return -1

        return predicted_class
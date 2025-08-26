from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
import pickle
from pathlib import Path

MODEL_PATH = Path("ml_step_time_model.pkl")


class StepTimePredictor:
    def __init__(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                self.model, self.vectorizer = pickle.load(f)
        else:
            self.model = None
            self.vectorizer = None

    def train(self, steps: list[str], times: list[int]):
        """Train a simple linear regression on step text -> duration"""
        self.vectorizer = TfidfVectorizer()
        X = self.vectorizer.fit_transform(steps)
        self.model = LinearRegression()
        self.model.fit(X, times)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump((self.model, self.vectorizer), f)

    def predict(self, step: str) -> int:
        """Predict duration for a single step"""
        if not self.model or not self.vectorizer:
            return 5  # fallback default
        X = self.vectorizer.transform([step])
        return max(1, int(self.model.predict(X)[0]))  # at least 1 min

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    product_id: str
    title: str
    brand: str
    price: float
    rating: float
    category: str
    description: str


@dataclass
class Review:
    review_id: str
    product_id: str
    text: str
    rating: float
    verified: bool


@dataclass
class QA:
    qa_id: str
    product_id: str
    question: str
    answer: str

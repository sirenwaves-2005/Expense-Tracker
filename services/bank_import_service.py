import csv, re, uuid
from datetime import date

MERCHANT_RULES = [
    (r'uber|lyft|ola|rapido|metro|bus|train|fuel|petrol|shell|bp |caltex', 'Transport'),
    (r'swiggy|zomato|mcdonalds|kfc|pizza|dominos|subway|restaurant|cafe|starbucks', 'Food & Dining'),
    (r'amazon|flipkart|myntra|ajio|nykaa|snapdeal', 'Shopping'),
    (r'electricity|water bill|gas bill|internet|jio|airtel|bsnl|vodafone', 'Utilities'),
    (r'apollo|medplus|1mg|pharmacy|hospital|clinic|doctor|health', 'Health'),
    (r'netflix|spotify|hotstar|prime|youtube|bookmyshow|pvr|inox', 'Entertainment'),
    (r'rent|housing|maintenance|society', 'Rent / Housing'),
    (r'bigbasket|blinkit|dmart|reliance fresh|grofer', 'Groceries'),
    (r'udemy|coursera|byju|unacademy|school|college|tuition', 'Education'),
    (r'salon|parlour|spa|gym|fitness', 'Personal Care'),
    (r'adobe|canva|microsoft 365|google play|apple', 'Subscriptions'),
]


import pandas as pd

data = {
    "Brand": ["TechNova", "EcoLife"],
    "Main Keyword": ["Wireless Earbuds", "Bamboo Toothbrush"],
    "Core Keyword": ["Bluetooth 5.0 Headphones", "Biodegradable Soft Bristles"],
    "Selling Points": ["Noise Cancelling, 24h Battery", "Pack of 4, BPA Free"],
    "Attributes": ["Black, Waterproof", "Natural Wood Handle"],
    "Scenarios": ["Gym, Commuting", "Family, Travel"]
}

df = pd.DataFrame(data)
df.to_excel("test_data.xlsx", index=False)
print("Created test_data.xlsx")

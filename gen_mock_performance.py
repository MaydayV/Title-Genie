import pandas as pd

def create_mock_perf():
    data = {
        "Product Name": [
            "TechNova Wireless Earbuds - Best Selling",
            "TechNova Bluetooth Headphones Waterproof",
            "EcoLife Bamboo Toothbrush Soft Bristles",
            "EcoLife Plastic Free Toothbrush",
            "Generic Bad Product"
        ],
        "Impressions": [1000, 800, 500, 400, 100],
        "Clicks": [50, 40, 30, 10, 0] # CTRs: 5%, 5%, 6%, 2.5%, 0%
    }
    df = pd.DataFrame(data)
    df.to_excel("mock_performance.xlsx", index=False)
    print("Created mock_performance.xlsx")

if __name__ == "__main__":
    create_mock_perf()

import pandas as pd

# Read correlation matrix
df = pd.read_csv('./results/correlation_matrix.csv', index_col=0)

# Convert to edge list with threshold filter
edges = []
countries = df.columns.tolist()

for i, country1 in enumerate(countries):
    for j, country2 in enumerate(countries[i+1:], i+1):
        corr = df.loc[country1, country2]
        # Skip if correlation is to or from "World"
        if country1 == 'World' or country2 == 'World':
            continue

        # # If this contains continents, skip those which have
        # # Subclasses available (e.g. remove "Africa" if it has "North Africa", "West Africa", etc.)
        # # Just continue for those cases
        # if 'Africa' == country1 or 'Africa' == country2:
        #     continue
        # if 'Asia' == country1 or 'Asia' == country2:
        #     continue
        # if 'Europe' == country1 or 'Europe' == country2:
        #     continue
        # if "Americas" == country1 or "Americas" == country2:
        #     continue

        # Keep correlations above threshold (adjust 0.3 as needed)
     #   if pd.notna(corr) and abs(corr) >= 0:
        edges.append({
            'Source': country1,
            'Target': country2,
            'Weight': corr
        })

# Save edge list for Gephi
edge_df = pd.DataFrame(edges)
edge_df.to_csv('./results/gephi_edges.csv', index=False)

print(f"Created {len(edges)} edges")
print(f"Saved to ./results/gephi_edges.csv")
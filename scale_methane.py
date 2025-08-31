import pandas as pd

df = pd.read_csv("ssp245_em_RCMIP.txt", sep ="\t", index_col=0, header=0)
print(df.head())
print(df[" CH4"]["2015"])
for col in df.columns:
    print(col)

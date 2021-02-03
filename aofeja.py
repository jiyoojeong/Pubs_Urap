import pandas as pd

dat = [{'a': 1, 'b': 2},
       {'a': 3, 'b': 4}]
df = pd.DataFrame(dat)

print(df)

df.drop(index=0, inplace=True)
print(df)
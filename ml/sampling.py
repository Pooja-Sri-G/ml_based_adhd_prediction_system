import pandas as pd
import numpy as np

df = pd.read_csv('adhd_original.csv')  


df['EducationStage'] = df['Age'].apply(lambda x: 1 if x < 6 else (2 if 6 <= x < 12 else (3 if 12 <= x < 18 else 4)))

# Separate classes
majority = df[df['ADHD'] == 1]
minority = df[df['ADHD'] == 0]

oversampled_minority = pd.concat([minority] * (len(majority) // len(minority) + 1), ignore_index=True).iloc[:len(majority)]

upsampled_df = pd.concat([majority, oversampled_minority], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)

upsampled_df.to_csv('adhd.csv', index=False)
print('Balanced dataset saved (50/50 ADHD, EducationStage corrected). Shape:', upsampled_df.shape)
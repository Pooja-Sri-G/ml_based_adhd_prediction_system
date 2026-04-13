
import pandas as pd
from imblearn.over_sampling import SMOTENC

df = pd.read_csv("adhd_original.csv")

TARGET_COL = "ADHD"
X = df.drop(columns=[TARGET_COL])
y = df[TARGET_COL]

CATEGORICAL_COLS = ["Gender", "EducationStage", "Medication", "SchoolSupport"]
feature_cols = list(X.columns)
categorical_indices = [feature_cols.index(c) for c in CATEGORICAL_COLS]

smote_nc = SMOTENC(
    categorical_features=categorical_indices,
    sampling_strategy={0: 2911, 1: 3307},
    random_state=42,
    k_neighbors=5,         
)

X_resampled, y_resampled = smote_nc.fit_resample(X, y)

df_resampled = pd.DataFrame(X_resampled, columns=feature_cols)
df_resampled[TARGET_COL] = y_resampled

int_cols = ["Age", "ImpulsivityScore", "Daydreaming", "RSD",
            "ComorbidAnxiety", "ComorbidDepression", "FamilyHistoryADHD",
            "ADHD"]
truly_int_cols = [c for c in int_cols if c != "ImpulsivityScore"]
for col in truly_int_cols:
    df_resampled[col] = df_resampled[col].round().astype(int)

output_path = "adhd.csv"       
df_resampled.to_csv(output_path, index=False)

print("=== Upsampling complete ===")
print(f"Original shape : {df.shape}")
print("Class distribution:")
print(df_resampled[TARGET_COL].value_counts().rename("count").to_frame())
print()
print(f"Saved to: {output_path}")
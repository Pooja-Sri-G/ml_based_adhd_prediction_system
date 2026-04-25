import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.utils import resample
import warnings
warnings.filterwarnings('ignore')

from xgboost import XGBClassifier
from catboost import CatBoostClassifier

# ---------------- LOAD DATA ----------------
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, 'adhd.csv')
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip()

# ---------------- FEATURE ENGINEERING ----------------
def get_features(df):
    df_new = df.copy()
    
    df_new['SymptomSum'] = df_new['InattentionScore'] + df_new['HyperactivityScore'] + df_new['ImpulsivityScore']
    df_new['Inatt_Hyper_Inter'] = df_new['InattentionScore'] * df_new['HyperactivityScore']
    
    st_col = 'ScreenTimeHours' if 'ScreenTimeHours' in df_new.columns else 'ScreenTime'
    df_new['Screen_Sleep_Ratio'] = df_new[st_col] / (df_new['SleepHours'] + 0.1)
    
    df_new['Symptom_Age_Ratio'] = df_new['SymptomSum'] / (df_new['Age'] + 1)
    
    return df_new

data = get_features(data)

# ---------------- SPLIT ----------------
target = 'ADHD'
X = data.drop(target, axis=1)
y = data[target]

# Handle missing
for col in X.columns:
    if pd.api.types.is_numeric_dtype(X[col]):
        X[col] = X[col].fillna(X[col].median())
    else:
        X[col] = X[col].fillna('None')

# Encoding
for col in X.columns:
    if not pd.api.types.is_numeric_dtype(X[col]):
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------- BALANCING ----------------
train_data = pd.concat([X_train, y_train], axis=1)
maj = train_data[train_data[target] == 1]
min = train_data[train_data[target] == 0]

min_up = resample(min, replace=True, n_samples=len(maj), random_state=42)
train_bal = pd.concat([maj, min_up]).sample(frac=1, random_state=42)

X_train = train_bal.drop(target, axis=1)
y_train = train_bal[target]

# ---------------- SCALING ----------------
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# ---------------- BASE MODELS ----------------
rf  = RandomForestClassifier(n_estimators=500, random_state=42)
gb  = GradientBoostingClassifier(n_estimators=500, random_state=42)
xgb = XGBClassifier(n_estimators=500, learning_rate=0.01, max_depth=8, random_state=42)
cat = CatBoostClassifier(iterations=500, learning_rate=0.01, depth=8, verbose=False)

# ---------------- VOTING ENSEMBLE ----------------
voting_model = VotingClassifier(
    estimators=[
        ('rf', rf),
        ('gb', gb),
        ('xgb', xgb),
        ('cat', cat)
    ],
    voting='soft'
)

# ---------------- STACKING ENSEMBLE ----------------
stacking_model = StackingClassifier(
    estimators=[
        ('rf', rf),
        ('gb', gb),
        ('xgb', xgb),
        ('cat', cat)
    ],
    final_estimator=LogisticRegression()
)

# ---------------- METRICS FUNCTION ----------------
def evaluate(model, name):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec  = recall_score(y_test, y_pred)
    f1   = f1_score(y_test, y_pred)
    
    try:
        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    except:
        auc = float('nan')
    
    print(f"\n{name}")
    print("-"*50)
    print(f"Accuracy : {acc*100:.2f}%")
    print(f"Precision: {prec*100:.2f}%")
    print(f"Recall   : {rec*100:.2f}%")
    print(f"F1 Score : {f1*100:.2f}%")
    print(f"ROC-AUC  : {auc*100:.2f}%" if not np.isnan(auc) else "ROC-AUC  : N/A")

# ---------------- RUN ----------------
print("\nENSEMBLE MODEL RESULTS")

evaluate(voting_model, "Voting Ensemble")
evaluate(stacking_model, "Stacking Ensemble")
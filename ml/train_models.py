import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.utils import resample
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    recall_score,
    precision_score,
    roc_auc_score,
    confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

print("\n[1/8] Loading data...")
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, 'adhd.csv')
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip()

def get_features(df):
    df_new = df.copy()
    
    df_new['SymptomSum'] = df_new['InattentionScore'] + df_new['HyperactivityScore'] + df_new['ImpulsivityScore']
    df_new['Inatt_Hyper_Inter'] = df_new['InattentionScore'] * df_new['HyperactivityScore']
    
    st_col = 'ScreenTimeHours' if 'ScreenTimeHours' in df_new.columns else 'ScreenTime'
    df_new['Screen_Sleep_Ratio'] = df_new[st_col] / (df_new['SleepHours'] + 0.1)
    
    df_new['Symptom_Age_Ratio'] = df_new['SymptomSum'] / (df_new['Age'] + 1)
    
    return df_new

data_engineered = get_features(data)

target = 'ADHD'
X = data_engineered.drop(target, axis=1)
y = data_engineered[target]

for col in X.columns:
    if pd.api.types.is_numeric_dtype(X[col]):
        X[col] = X[col].fillna(X[col].median())
    else:
        X[col] = X[col].fillna('None')

label_encoders = {}
for col in X.columns:
    if not pd.api.types.is_numeric_dtype(X[col]):
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

train_data = pd.concat([X_train, y_train], axis=1)
maj = train_data[train_data[target] == 1]
min = train_data[train_data[target] == 0]
min_up = resample(min, replace=True, n_samples=len(maj), random_state=42)
train_bal = pd.concat([maj, min_up]).sample(frac=1, random_state=42)
X_train_bal = train_bal.drop(target, axis=1)
y_train_bal = train_bal[target]

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_bal)
X_test_scaled = scaler.transform(X_test)

print("\n" + "="*65)
print("         INDIVIDUAL MODEL METRICS (on test set)")
print("="*65)
print(f"  {'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>7} {'ROC-AUC':>8}")
print("-"*65)

trained_models = {}

def get_metrics(model, X_tr, y_tr, X_te, y_te):
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    acc  = accuracy_score(y_te, y_pred)
    prec = precision_score(y_te, y_pred, zero_division=0)
    rec  = recall_score(y_te, y_pred, zero_division=0)
    f1   = f1_score(y_te, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
    except:
        auc = float('nan')
    return acc, prec, rec, f1, auc

def print_and_store_metrics(name, model, X_tr, y_tr, X_te, y_te):
    acc, prec, rec, f1, auc = get_metrics(model, X_tr, y_tr, X_te, y_te)
    auc_str = f"{auc*100:.2f}%" if not np.isnan(auc) else "  N/A"
    print(f"  {name:<22} {acc*100:>8.2f}%  {prec*100:>8.2f}%  {rec*100:>7.2f}%  {f1*100:>6.2f}%  {auc_str:>8}")
    trained_models[name] = {
        'model': model,
        'accuracy': acc,
        'precision': prec,
        'combined_score': (acc + prec) / 2
    }
    return model

rf = RandomForestClassifier(n_estimators=1000, random_state=42, class_weight='balanced')
gb = GradientBoostingClassifier(n_estimators=1000, learning_rate=0.01, max_depth=7, random_state=42)

rf = print_and_store_metrics("Random Forest",     rf, X_train_scaled, y_train_bal, X_test_scaled, y_test)
gb = print_and_store_metrics("Gradient Boosting", gb, X_train_scaled, y_train_bal, X_test_scaled, y_test)

if HAS_XGB:
    xgb = XGBClassifier(n_estimators=1000, learning_rate=0.01, max_depth=8, colsample_bytree=0.7, random_state=42)
    xgb = print_and_store_metrics("XGBoost", xgb, X_train_scaled, y_train_bal, X_test_scaled, y_test)

if HAS_CATBOOST:
    cat = CatBoostClassifier(iterations=1000, learning_rate=0.01, depth=8, random_state=42, verbose=False)
    cat = print_and_store_metrics("CatBoost", cat, X_train_scaled, y_train_bal, X_test_scaled, y_test)

print("-"*65)

best_model_name = max(trained_models, key=lambda k: trained_models[k]['combined_score'])
best_model_data = trained_models[best_model_name]
best_model = best_model_data['model']

print(f"\n[OK] Best Model Selected: {best_model_name}")
print(f"     Accuracy:  {best_model_data['accuracy']*100:.2f}%")
print(f"     Precision: {best_model_data['precision']*100:.2f}%")

y_pred_best = best_model.predict(X_test_scaled)
print("\nDetailed Classification Report (Best Model):")
print(classification_report(y_test, y_pred_best, target_names=["No ADHD", "ADHD"]))

joblib.dump(best_model, 'adhdModel.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoders, 'labelEncoders.pkl')

print("\nDone. Models saved.")
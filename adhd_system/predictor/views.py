import joblib
import os
import json
import csv
from django.shortcuts import render 
from django.http import HttpResponse
from .generate_report import generate_adhd_report

base = os.path.dirname(os.path.abspath(__file__))
scaler = joblib.load(os.path.join(base, 'scaler.pkl'))
label_encoders = joblib.load(os.path.join(base, 'labelEncoders.pkl'))
adhd_model = joblib.load(os.path.join(base, 'adhdModel.pkl'))

def predict(request):
    if request.method == 'POST':
        # Collect raw assessment data with proper validation
        try:
            user_data_raw = {
                'age': int(request.POST.get('age', 0)),
                'Gender': request.POST.get('Gender', 'Male'),
                'EducationStage': request.POST.get('EducationStage', 'Adult'),
                'HyperactivityScore': float(request.POST.get('HyperactivityScore', 0)),
                'DayDreaming': int(request.POST.get('DayDreaming', 0)),
                'RSD': int(request.POST.get('RSD', 0)),
                'SleepHours': float(request.POST.get('SleepHours', 7)),
                'ScreenTime': float(request.POST.get('ScreenTime', 3)),
                'ComorbidAnxiety': int(request.POST.get('ComorbidAnxiety', 0)),
                'ComorbidDepression': int(request.POST.get('ComorbidDepression', 0)),
                'FamilyHistoryADHD': int(request.POST.get('FamilyHistoryADHD', 0)),
                'SchoolSupport': request.POST.get('SchoolSupport', 'None'),
                'Medication': request.POST.get('Medication', 'No'),
                'AcademicScore': float(request.POST.get('AcademicScore', 70)),
                'InattentionScore': float(request.POST.get('InattentionScore', 0)),
                'ImpulsivityScore': float(request.POST.get('ImpulsivityScore', 0)),
            }
        except (ValueError, TypeError) as e:
            print(f"Data conversion error: {e}")
            return render(request, 'index.html', {'error': 'Invalid form data. Please check your entries.'})

        # Go/No-Go game data for the report
        game_data = {
            'total_trials': int(request.POST.get('total_trials', 0)),
            'correct_go': int(request.POST.get('correct_go', 0)),
            'missed_go': int(request.POST.get('missed_go', 0)),
            'correct_inhibit': int(request.POST.get('correct_inhibit', 0)),
            'commission_errors': int(request.POST.get('commission_errors', 0)),
            'reaction_times': json.loads(request.POST.get('reaction_times', '[]'))
        }

        # ── Time game data for the report ──────────────────────────────────
        # time_game_rounds is a JSON array of {target_ms, actual_ms} objects
        # sent by time_game.js via the hidden field in index.html
        try:
            raw_rounds = json.loads(request.POST.get('time_game_rounds', '[]'))
        except (json.JSONDecodeError, TypeError):
            raw_rounds = []

        time_game_data = {'rounds': raw_rounds}
        # ───────────────────────────────────────────────────────────────────

        # Transform features for model prediction with error handling
        try:
            gender_enc    = label_encoders['Gender'].transform([user_data_raw['Gender']])[0]
            education_enc = label_encoders['EducationStage'].transform([user_data_raw['EducationStage']])[0]
            medication_enc = label_encoders['Medication'].transform([user_data_raw['Medication']])[0]
            school_enc    = label_encoders['SchoolSupport'].transform([user_data_raw['SchoolSupport']])[0]
        except (KeyError, ValueError) as e:
            print(f"Label encoding error: {e}")
            return render(request, 'index.html', {'error': 'Error processing your assessment. Please try again.'})

        symptomsum        = user_data_raw['InattentionScore'] + user_data_raw['HyperactivityScore'] + user_data_raw['ImpulsivityScore']
        inatt_hyper_inter = user_data_raw['InattentionScore'] * user_data_raw['HyperactivityScore']
        screen_sleep_ratio = user_data_raw['ScreenTime'] / (user_data_raw['SleepHours'] + 0.1)
        symptom_age_ratio = symptomsum / (user_data_raw['age'] + 1)

        features = [
            user_data_raw['age'],
            gender_enc,
            education_enc,
            user_data_raw['InattentionScore'],
            user_data_raw['HyperactivityScore'],
            user_data_raw['ImpulsivityScore'],
            symptomsum,
            user_data_raw['DayDreaming'],
            user_data_raw['RSD'],
            user_data_raw['SleepHours'],
            user_data_raw['ScreenTime'],
            user_data_raw['ComorbidAnxiety'],
            user_data_raw['ComorbidDepression'],
            user_data_raw['FamilyHistoryADHD'],
            medication_enc,
            school_enc,
            user_data_raw['AcademicScore'],
            inatt_hyper_inter,
            screen_sleep_ratio,
            symptom_age_ratio
        ]

        X = scaler.transform([features])
        prediction = int(adhd_model.predict(X)[0])

        # Store everything in session for report generation
        request.session['assessment_report_data'] = {
            'user_data': {
                'Age': user_data_raw['age'],
                'Gender': user_data_raw['Gender'],
                'EducationStage': user_data_raw['EducationStage'],
                'InattentionScore': user_data_raw['InattentionScore'],
                'ImpulsivityScore': user_data_raw['ImpulsivityScore'],
                'HyperactivityScore': user_data_raw['HyperactivityScore'],
                'Daydreaming': user_data_raw['DayDreaming'],
                'RSD': user_data_raw['RSD'],
                'SleepHours': user_data_raw['SleepHours'],
                'ScreenTime': user_data_raw['ScreenTime'],
                'ComorbidAnxiety': user_data_raw['ComorbidAnxiety'],
                'ComorbidDepression': user_data_raw['ComorbidDepression'],
                'FamilyHistoryADHD': user_data_raw['FamilyHistoryADHD'],
                'Medication': user_data_raw['Medication'],
                'SchoolSupport': user_data_raw['SchoolSupport'],
                'AcademicScore': user_data_raw['AcademicScore'],
            },
            'game_data': game_data,
            'time_game_data': time_game_data,   # ← NEW
            'prediction': prediction,
            'user_name': request.POST.get('full_name', 'User')
        }

        result_text = "There are possible signs of ADHD from your answers." if prediction == 1 else "You might not have ADHD"

        try:
            project_root = os.path.dirname(os.path.dirname(base))
            dataset_path = os.path.join(project_root, 'ml', 'adhd.csv')
            row_data = [
                user_data_raw['age'], user_data_raw['Gender'], user_data_raw['EducationStage'],
                user_data_raw['InattentionScore'], user_data_raw['HyperactivityScore'],
                user_data_raw['ImpulsivityScore'], symptomsum, user_data_raw['DayDreaming'],
                user_data_raw['RSD'], user_data_raw['SleepHours'], user_data_raw['ScreenTime'],
                user_data_raw['ComorbidAnxiety'], user_data_raw['ComorbidDepression'],
                user_data_raw['FamilyHistoryADHD'], user_data_raw['Medication'],
                user_data_raw['SchoolSupport'], user_data_raw['AcademicScore'], prediction
            ]
            with open(dataset_path, mode='a', newline='') as file:
                csv.writer(file).writerow(row_data)
        except Exception as e:
            print(f"Error saving to dataset: {e}")

        return render(request, "result.html", {"prediction": prediction, "result": result_text})

    return render(request, "index.html")

def download_report(request):
    data = request.session.get('assessment_report_data')
    if not data:
        return HttpResponse("No assessment data found. Please complete the assessment first.", status=400)

    pdf_bytes = generate_adhd_report(
        data['user_data'],
        data['game_data'],
        data['prediction'],
        user_name=data.get('user_name', 'User'),
        time_game_data=data.get('time_game_data', {})
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ADHD_Assessment_Report.pdf"'
    response['Content-Length'] = len(pdf_bytes)
    return response

def game(request):
    return render(request, "game.html")

def time_game(request):
    return render(request, "time_game.html")
import traceback
import sys
import os

sys.path.append(os.path.dirname(__file__))

from predictor.generate_report import generate_adhd_report

sample_user={'Age':22,'Gender':'Male','EducationStage':'University'}
game_data={'total_trials':10}
time_game_data={'rounds':[]} # empty rounds

try:
    generate_adhd_report(sample_user, game_data, 1, 'Alex', time_game_data)
    with open('trace.txt', 'w') as f:
        f.write("SUCCESS")
except Exception as e:
    with open('trace.txt', 'w') as f:
        traceback.print_exc(file=f)

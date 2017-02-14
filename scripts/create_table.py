"""
Create a user study statistics table for the user study data.
"""

from website.models import *

def create_stat_table(output_path):
    with open(output_path, 'w') as o_f:
        # write column names
        o_f.write('Time,CR,Subject,Task,Treatment,Order\n')

        for user in User.objects.all():
            if len(user.access_code) > 3 and user.num_sessions_completed >= 1:
                # find the user's most recently finished study session
                finished_study_session = None
                for study_session in StudySession.objects.filter(user=user,
                    status='finished').order_by('creation_time'):
                    finished_study_session = study_session
                stage_i_total_time = finished_study_session.stage_total_time_spent('I')
                completion_rate = finished_study_session.stage_completion_rate('I')
                task = '0' if finished_study_session.task_block_order == '0' else '1'
                treatment = 'A' if finished_study_session.treatment_order == '0' else 'B'
                order = 'I'
                o_f.write('{},{},{},{},{}\n'.format(stage_i_total_time.seconds,
                                                    completion_rate,
                                                    user.access_code,
                                                    task, treatment, order))
                stage_ii_total_time = finished_study_session.stage_total_time_spent('II')
                completion_rate = finished_study_session.stage_completion_rate('II')
                task = '1' if finished_study_session.task_block_order == '0' else '0'
                treatment = 'B' if finished_study_session.treatment_order == '0' else 'A'
                order = 'II'
                o_f.write('{},{},{},{},{}\n'.format(stage_ii_total_time.seconds,
                                                    completion_rate,
                                                    user.access_code,
                                                    task, treatment, order))
        o_f.close()

def run():
    create_stat_table('user_study_table_time.csv')

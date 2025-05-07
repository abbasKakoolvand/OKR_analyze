def is_day_in_db(session, Tasks, day_str):
    result = session.query(Tasks).filter(Tasks.day == day_str).first()
    return result is not None


def is_task_kr_person_exist(session, TaskScore, kr_code, person):
    result = session.query(TaskScore).filter(
        TaskScore.kr_code == kr_code,
        TaskScore.person == person  # ❌ This will fail - no 'person' column in TaskScore
    ).first()
    return result is not None


def get_person_tasks(session, Tasks, person):
    tasks_for_person = session.query(Tasks).filter_by(person=person).all()
    return tasks_for_person


def get_unique_persons(session, Tasks):
    try:
        # Query for unique persons
        unique_persons = session.query(Tasks.person).distinct().all()

        # Convert query results from tuples to strings
        # Result looks like: [('rezazadeh',), ('farmani',), ...]
        person_list = [person[0] for person in unique_persons]

        return sorted(person_list)  # Sort alphabetically

    except Exception as e:
        print(f"Error retrieving persons: {str(e)}")


def save_scores_in_db(scored_tasks, session, taskscore, kr_code, person):
    score_records = [
        taskscore(
            task_id=task_id,
            kr_code=kr_code,
            score=scored_tasks[task_id],
            person=person,
        ) for task_id in scored_tasks.keys()
    ]

    # Bulk insert
    session.bulk_save_objects(score_records)
    session.commit()

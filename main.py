import json,os,requests

path = os.path.dirname(os.path.abspath(__file__))
webhook_url = os.getenv('WEBHOOK_AC_NOTIFY')
problems_url = 'https://kenkoooo.com/atcoder/resources/problems.json'
problems_path = path + '/problems.json'
problem_models_url = 'https://kenkoooo.com/atcoder/resources/problem-models.json'
problem_models_path = path + '/problem-models.json'
user_url= 'https://kenkoooo.com/atcoder/atcoder-api/results?user={}'
user_path = path + '/{}.json'

def get_color(diff):
    if diff is None or diff < 400: return '#808080'
    elif diff <  800: return '#804000'
    elif diff < 1200: return '#008000'
    elif diff < 1600: return '#00C0C0'
    elif diff < 2000: return '#0000FF'
    elif diff < 2400: return '#C0C000'
    elif diff < 2800: return '#FF8000'
    else: return '#FF0000'

def get_json(color, user, contest_id, problem_id, title, diff):
    return {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "{} が <https://atcoder.jp/contests/{}/tasks/{}|{}> をACしたよ:muscle:\n*Difficulty* {}".format(user, contest_id, problem_id, title, diff)
                        }
                    }
                ]
            }
        ]
    }

def main():
    # load problems.json for title (download if not present)
    try:
        problems_json = json.load(open(problems_path))
    except FileNotFoundError:
        with open(problems_path, 'w') as f:
            json.dump(problems_json := requests.get(problems_url).json(), f)
    # load problem-models.json for difficulty (download if not present)
    try:
        problem_models_json = json.load(open(problem_models_path))
    except FileNotFoundError:
        with open(problem_models_path, 'w') as f:
            json.dump(problem_models_json := requests.get(problem_models_url).json(), f)
    # load users.txt
    users_file = open(path + '/users.txt', 'r')

    while line := users_file.readline():
        user = line.strip()
        try: # if [user].json does not exist, download and finish
            user_local_json = json.load(open(user_path.format(user)))
            user_json = requests.get(user_url.format(user)).json()
            # submissions = user_json \ user_local_json
            submissions = [sub for sub in user_json 
                if sub not in user_local_json and sub['result'] == 'AC']
            with open(user_path.format(user), 'w') as f:
                json.dump(user_json, f)
            # re-download if submission problem_id does not exist in problems.json
            if any([len([p for p in problems_json if p['id'] == sub['problem_id']]) == 0 for sub in submissions]):
                with open(problems_path, 'w') as f:
                    json.dump(problems_json := requests.get(problems_url).json(), f)
            # re-download if submission problem_id does not exist in problem-models.json
            if any([sub['problem_id'] not in problem_models_json.keys() for sub in submissions]):
                with open(problem_models_path, 'w') as f:
                    json.dump(problem_models_json := requests.get(problem_models_url).json(), f)
            for submission in submissions:
                problem_model = problem_models_json.get(submission['problem_id'])
                diff = problem_model['difficulty'] if problem_model != None else None
                color = get_color(diff)
                contest_id, problem_id = submission['contest_id'], submission['problem_id']
                title = t[0] if (t := [p['title'] for p in problems_json if p['id'] == submission['problem_id']]) != [] else None
                requests.post(webhook_url, data = json.dumps(get_json(color, user, contest_id, problem_id, title, diff)))
        except FileNotFoundError:
            with open(user_path.format(user), 'w') as f:
                json.dump(requests.get(user_url.format(user)).json(), f)

    users_file.close()

if __name__ == '__main__':
    main()

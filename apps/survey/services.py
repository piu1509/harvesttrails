import requests

def get_survey():
    url = 'http://localhost:8000/api/questions/'
    r = requests.get(url)
    survey = r.json()
    print(survey)
    survey_list = []
    # for i in range(len(survey['survey'])):
    #     survey_list.append(survey['survey'][i])
    # return survey_list
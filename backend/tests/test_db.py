import json
from uuid import uuid4


def test_list_jobs(client, mocker):
    mocker.patch('src.app.get_jobs', return_value=[{'id': 'mock_id', 'status': 'running'}])
    response = client.get('/api/jobs')
    assert response.status_code == 200
    assert response.json[0]['id'] == 'mock_id'

def test_start_crawler(client, mocker):
    mock_create = mocker.patch('src.app.create_job', return_value={'id': uuid4()})
    mock_publish = mocker.patch('src.app.publish_crawler_event', return_value=True)
    mock_update = mocker.patch('src.app.update_job')

    response = client.post('/start-crawler', data=json.dumps({
        'domain': 'example.com',
        'depth': 1
    }), content_type='application/json')

    assert response.status_code == 202
    mock_create.assert_called_once()
    mock_publish.assert_called_once()
    mock_update.assert_called_once()

def test_get_job(client, mocker):
    job_id = uuid4()
    mocker.patch('src.app.get_job', return_value={'id': str(job_id), 'status': 'running'})
    response = client.get(f'/api/jobs/{job_id}')
    assert response.status_code == 200
    assert response.json['id'] == str(job_id)

def test_delete_job(client, mocker):
    job_id = uuid4()
    mocker.patch('src.app.delete_job', return_value=True)
    response = client.delete(f'/api/jobs/{job_id}')
    assert response.status_code == 200
    assert response.json['message'] == 'Job deleted successfully'

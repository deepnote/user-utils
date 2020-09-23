def setNotebookPath():
    import os
    import sys
    import json
    import IPython
    import requests
    from IPython.lib import kernel
    project_path = '/home/jovyan/work/'
    try:
        connection_file = os.path.basename(kernel.get_connection_file())
        kernel_id = connection_file.split('-', 1)[1].split('.')[0]
        r = requests.get('http://0.0.0.0:8888/api/sessions', headers={'Authorization': 'token  {}'.format(os.environ['JUPYTER_TOKEN']), 'Content-type': 'application/json'})
        relative_notebook_path = next(session['path'] for session in json.loads(r.text) if session['kernel']['id'] == kernel_id)
        dirPath = os.path.dirname(os.path.abspath(project_path + relative_notebook_path))
        sys.path = list(filter(lambda path: not path.startswith(project_path), sys.path))
        if dirPath not in sys.path: sys.path.append(dirPath)
        os.chdir(dirPath)
    except:
        pass

setNotebookPath()
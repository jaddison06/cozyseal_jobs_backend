import flask as f
from flask import request, jsonify, send_file
import json
import os.path as path
import os

app = f.Flask(__name__)

app.config['DEBUG'] = True

# base for all app routes
BASE_ROUTE = '/jobs'

@app.route('/', methods=['GET'])
def root():
    return 'server online'

def getJobFolder(jobID):
    return f'./jobs/{jobID}'

def getJobFile(jobID):
    return f'{getJobFolder(jobID)}/job.json'

def jobFileExists(jobID):
    return path.exists(getJobFile(jobID))

def getJob(jobID):
    if not jobFileExists(jobID): return {}
    with open(getJobFile(jobID), 'rt') as fh:
        return json.loads(fh.read())

def writeJob(jobID, data):
    if not jobFileExists(jobID): return
    with open(getJobFile(jobID), 'wt') as fh:
        fh.write(json.dumps(data, indent=2))

def checkArgs(requestArgs, argsToCheck = {'jobID': int}):
    out = []
    
    for item in list(argsToCheck.keys()):
        if item in requestArgs:
            try:
                val = argsToCheck[item](requestArgs[item])
            except ValueError:
                return f'Error - field "{item}" is of incorrect type'
            out.append(val)
        else:
            return 'Error - please specify a "{item}" field'
    
    return out

def getAssets(jobID):
    out = {}
    jobFolder = getJobFolder(jobID)
    for entry in os.listdir(f'{jobFolder}/assets'):
        fullPath = f'{jobFolder}/assets/{entry}'
        if path.isfile(fullPath):
            out[path.basename(entry)] = fullPath
    
    return out

@app.route(f'{BASE_ROUTE}/checkout', methods=['GET'])
def checkoutJob():

    id = checkArgs(request.args)
    if type(id) == str: return id
    id = id[0]
    
    job = getJob(id)

    return jsonify(job)

@app.route(f'{BASE_ROUTE}/retrieveAsset', methods=['GET'])
def getAsset():
    info = checkArgs(request.args, {
        'jobID': int,
        'assetName': str
    })
    if type(info) == str: return info

    id = info[0]
    assetName = info[1]

    assets = getAssets(id)
    if not assetName in list(assets.keys()):
        return f'Error - no such asset {assetName} for job {id}'


    return send_file(
        assets[assetName],
        mimetype=f'image/{path.splitext(assetName)[1][1:]}'
    )


@app.route(f'{BASE_ROUTE}/', methods=['GET'])
def getJobStatus():
    id = checkArgs(request.args)
    if type(id) == str: return id
    id = id[0]

    job = getJob(id)
    jobExists = jobFileExists(id)

    if jobExists:
        jobComplete = getJob(id)['complete']
    else:
        jobComplete = False;

    return jsonify({
        "exists": jobExists,
        "complete": jobComplete
    })


@app.route(f'{BASE_ROUTE}/return', methods=['POST'])
def returnJob():
    id = checkArgs(request.args)
    if type(id) == str: return id
    id = id[0]

    if not request.json: return ''

    writeJob(id, request.json)

    return ''


app.run(ssl_context='adhoc', host='0.0.0.0', port=5000)
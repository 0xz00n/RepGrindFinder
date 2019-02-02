#! /usr/bin/python

import os, sys, json, time, numpy, urllib, zipfile
from scipy import spatial
from collections import Counter

def downloader(directory,nf=0):
    popSysLoc = os.path.join(directory, 'systems_populated.json')
    stationsLoc = os.path.join(directory, 'stations.json')
    dFile = urllib.URLopener()
    print '[*] Downloading latest data from eddb.io...'
    try:
        dFile.retrieve('https://eddb.io/archive/v5/systems_populated.json', popSysLoc)
        dFile.retrieve('https://eddb.io/archive/v5/stations.json', stationsLoc)
        print '[*] Done'
    except:
        if nf == 1:
            ans = raw_input('[!] Unable to download latest data, continue with old data? [Y/n]\n')
            print ''
            if ans == 'y' or ans == 'Y' or ans == '':
                return
            else:
                print '[!] Exiting'
                sys.exit()
        else:
            print '[!] Data not found locally and unable to download from eddb.io, exiting'
            sys.exit()

def checkAge(directory,filename):
    print '[*] Checking that eddb.zip exists and is recent...'
    path = os.path.join(directory, filename)
    if os.path.isfile(path):
        fileAge = int(os.path.getmtime(path))
        now = int(time.time())
        if (now - fileAge) > 86400:
            ans = raw_input('[!] Data is older than 24 hours, download latest? [Y/n]\n')
            print ''
            if ans == 'y' or ans == 'Y' or ans == '':
                os.remove(path)
                downloader(directory)
                rezip(directory,filename)
    else:
        print '[!] File eddb.zip not found'
        nf = 1
        downloader(directory,nf)
        rezip(directory,filename)
        for root, dirs, files, in os.walk(directory):
            for f in files:
                if f.endswith('.json'):
                    rPath = os.path.join(directory, f)
                    os.remove(rPath)
        return
    print '[*] Done'

def unzip(directory,filename):
    print '[*] Extracting files to be read...'
    path = os.path.join(directory, filename)
    tar = os.path.join(directory)
    archive = zipfile.ZipFile(path, 'r')
    for f in archive.namelist():
        if f.endswith('.json'):
            archive.extract(f, tar)
            print '[*] Extracted %s' % f
    print '[*] Done'

def rezip(directory,filename):
    print '[*] Compressing files...'
    path = os.path.join(directory, filename)
    for root, dirs, files in os.walk(directory):
        with zipfile.ZipFile(path, 'w') as zipper:
            for f in files:
                if f.endswith('.json'):
                    tar = os.path.join(directory, f)
                    zipper.write(tar, os.path.basename(tar))
    print '[*] Done'

def jsonLoader(directory,filename):
    print '[*] Loading %s into memory' % filename
    path = os.path.join(directory, filename)
    imp = open(path, 'r').read()
    loader = json.loads(imp)
    print '[*] Done'
    return loader

def jsonRemover():
    for root, dirs, files in os.walk('jsons'):
        for f in files:
            if f.endswith('.json'):
                rPath = os.path.join('jsons',f)
                os.remove(rPath)

def distCalc(x1,y1,z1,x2,y2,z2):
    p1 = numpy.array([x1,y1,z1])
    p2 = numpy.array([x2,y2,z2])
    dist = numpy.linalg.norm(p1-p2)
    return dist

def arrCreate(tarJson):
    coordArray = []
    for system in tarJson:
        coordArray.append([float(system['x']), float(system['y']), float(system['z'])])
    return coordArray

def bubbleFind(coordList,tarJson,stationJson):
    i = 0
    bubbleTree = spatial.KDTree(coordList)
    print '[*] Compiling list of system pairs that have only 1 other populated system within 10Ly'
    for system in tarJson:
        x1 = float(system['x'])
        y1 = float(system['y'])
        z1 = float(system['z'])
        result = bubbleTree.query_ball_point([x1,y1,z1], 10)
        if len(result) == 2:
            if result[0] == i:
                j = 0
                for system2 in tarJson:
                    if system2['id'] == tarJson[result[1]]['id']:
                        x2 = float(system2['x'])
                        y2 = float(system2['y'])
                        z2 = float(system2['z'])
                        result2 = bubbleTree.query_ball_point([x2,y2,z2], 10)
                        if len(result2) == 2:
                            if system['allegiance'] == 'Federation' and system2['allegiance'] == 'Federation':
                                stationArray = stationFind(stationJson,system)
                                stationArray2 = stationFind(stationJson,system2)
                                if stationArray is not None and stationArray2 is not None:
                                    if len(stationArray) == 1 and len(stationArray2) == 1:
                                        print ''
                                        print 'From',system['name'],'to',system2['name'],':',round(float(distCalc(x1,y1,z1,x2,y2,z2)),2),'Ly'
                                        print 'Economic State In Order:'
                                        print stationArray[0][2]
                                        print stationArray2[0][2]
                    j += 1
            else:
                j = 0
                for system2 in tarJson:
                    if system2['id'] == tarJson[result[0]]['id']:
                        x2 = float(system2['x'])
                        y2 = float(system2['y'])
                        z2 = float(system2['z'])
                        result2 = bubbleTree.query_ball_point([x2,y2,z2], 10)
                        if len(result2) == 2:
                            if system['allegiance'] == 'Federation' and system2['allegiance'] == 'Federation':
                                stationArray = stationFind(stationJson,system)
                                stationArray2 = stationFind(stationJson,system2)
                                if stationArray is not None and stationArray2 is not None:
                                    if len(stationArray) == 1 and len(stationArray2) == 1:
                                        print ''
                                        print 'From',system['name'],'to',system2['name'],':',round(float(distCalc(x1,y1,z1,x2,y2,z2)),2),'Ly'
                                        print 'Economic State In Order:'
                                        print stationArray[0][2]
                                        print stationArray2[0][2]
                    j += 1
        i += 1

def stationFind(stations,system):
    stations2 = stations
    stationArray = []
    for station in stations:
        if system['id'] == station['system_id']:
            if 'Planetary' not in station['type']:
                stationArray.append([station['system_id'],station['name'],station['state']])
    count = Counter(elem[0] for elem in stationArray)
    if count[system['id']] == 1:
        for station2 in stations2:
            if system['id'] == station2['system_id']:
                if 'Planetary' not in station2['type']:
                    if 'L' in station2['max_landing_pad_size']:
                        return stationArray
    else:
        stationArray = []
        return stationArray

checkAge('jsons','eddb.zip')
unzip('jsons','eddb.zip')
popSys = jsonLoader('jsons','systems_populated.json')
stations = jsonLoader('jsons','stations.json')
coordList = arrCreate(popSys)
bubbleFind(coordList,popSys,stations)
jsonRemover()

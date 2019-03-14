# -*- coding: utf-8 -*-
from __future__ import print_function
import pickle
import os.path
import httplib2
import sys
from googleapiclient.discovery import build
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def upload_file(service, src_path, dst_path):
    parents_id = {}
    predir = ""
    for folder in dst_path.split('/'):
        if predir not in parents_id.keys():
            predir = ""
        else:
            predir = parents_id[predir]

        if predir != "":   
            find = service.files().list(q="name = '%s'and \
            mimeType = 'application/vnd.google-apps.folder' and \
            '%s' in parents and \
            trashed != True" %(folder, predir)).execute()
        else:
            find = service.files().list(q="name = '%s'and \
            mimeType = 'application/vnd.google-apps.folder' and \
            trashed != True" %folder).execute()
            
        dirs = find.get('files', [])
        if len(dirs) == 0:
            if predir != "":
                dir_metadata = {'name': folder,
                            'parents': [predir],
                            'mimeType': 'application/vnd.google-apps.folder'}
            else:
                dir_metadata = {'name': folder,
                            'mimeType': 'application/vnd.google-apps.folder'}
            newdir = service.files().create(body = dir_metadata,
                                            fields = 'id').execute()
            parents_id[folder] = newdir.get('id', [])
            predir = folder
        else:
            parents_id[folder] = dirs[0].get('id')
            predir = folder
            
    if predir != "":
        file_metadata = {'name': src_path.split('/')[-1],
                         'parents': [parents_id[predir]]}
    else:
        file_metadata = {'name': src_path.split('/')[-1]}
    
    media = MediaFileUpload(src_path)
    file = service.files().create(body = file_metadata,
                                  media_body = media,
                                  fields = 'id').execute()
        
    return True

def download_file(service, src_path, dst_path):
    parents_id = {}
    predir = ""
    for folder in src_path.split('/')[:-1]:
        if predir not in parents_id.keys():
            predir = ""
        else:
            predir = parents_id[predir]

        if predir != "":   
            find = service.files().list(q="name = '%s'and \
            mimeType = 'application/vnd.google-apps.folder' and \
            '%s' in parents and \
            trashed != True" %(folder, predir)).execute()
        else:
            find = service.files().list(q="name = '%s'and \
            mimeType = 'application/vnd.google-apps.folder' and \
            trashed != True" %folder).execute()
            
        dirs = find.get('files', [])
        if len(dirs) == 0:
            print('No such file on Google Drive!')
            return False
        else:
            parents_id[folder] = dirs[0].get('id')
            predir = folder

    filename = src_path.split('/')[-1]
    find = service.files().list(q="name = '%s'and \
    mimeType != 'application/vnd.google-apps.folder'and \
    '%s' in parents and \
    trashed != True" %(filename, parents_id[predir])).execute()

    files = find.get('files', [])
    if len(files) == 0:
        print('No such file on Google Drive!')
        return False
    else:
        request = service.files().get_media(fileId=files[0].get('id'))
        if dst_path[-1] != "/":
            dst_path = dst_path + "/"
        fh = io.FileIO(dst_path + filename, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

def main(cmd, src_path, dst_path):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    if cmd != 'put' and cmd != 'get':
        print('No such command!')
        sys.exit()
    
    if cmd == 'put':
        if not os.path.exists(src_path):
            print('No such file: ', src_path)
            sys.exit()

        if upload_file(service, src_path, dst_path):
            print('Success!')
            
    elif cmd == 'get':
        if not os.path.exists(dst_path):
            print('No such directory: ', dst_path)
            sys.exit()
        
        if download_file(service, src_path, dst_path):
            print('Succes!')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Too few parameters! For example: <python GDriveTest.py put doc.txt folder>')
        sys.exit()
    elif len(sys.argv) > 4:
        print('Too many parameters! For example: <python GDriveTest.py put doc.txt folder>')
        sys.exit()
    cmd = sys.argv[1]
    src_path = sys.argv[2]
    dst_path = sys.argv[3]
    main(cmd, src_path, dst_path)

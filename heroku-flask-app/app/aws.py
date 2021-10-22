import boto3
import os
import json
#from requests_toolbelt.multipart import decoder
from botocore.config import Config
import glob
from time import perf_counter
import threading

def timed(num_reps):
    """
    Decorator to check average function performance over a preconfigured time duration.
    """
    from functools import wraps
    print(f"Timing for {num_reps}")
    def dec_time(fn):
        from time import perf_counter
        @wraps(fn)
        def inner(*args, **kwargs):
            total_elapsed = 0
            for i in range(num_reps):
                start = perf_counter()
                result = fn(*args, **kwargs)
                end = perf_counter()
                total_elapsed += (end - start)
            avg_elapsed = total_elapsed / num_reps
            print(f'Average Run time for {num_reps} repetitions: {avg_elapsed:.3f}s')
            return result
        return inner
    return dec_time


class S3Handler():
    '''
        AWS S3 bucket handler. 
        Creates a singleton instance
    '''
    def __init__(self):
        self.s3_obj = boto3.client('s3', 
                                   aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                                   aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        self.s3_bucket = os.environ.get('S3_DEFAULT_BUCKET')
        self.history_file = "history.json"
        self.history_json = self.read_history()

    def __create_base_history__(self):
        '''
            Creates the base history.json file when the application 
            gets initialized for the first time.
        '''
        # with open('./static/text/history.','w') as historyf:
        default_history = []
        history_filename = os.path.join('./static/text', self.history_file)
        with open(history_filename, 'w') as f:
            for file_entry in glob.glob("./static/saved_imgs/*jpg"):
                item = { "id":"base", "path":file_entry, "class":"N/A","confidence":"10"}
                default_history.append(item)
                f.write(json.dumps(item) + "\n")
        # f.close()
        self.upload_to_s3(history_filename, 
                    os.path.basename(self.history_file)
                )

        return default_history
    
    @timed(1)
    def upload_to_s3(self, file_name, obj_name_s3):
        '''
        Uploads a single file to S3 
        '''
        local_s3_obj = boto3.client('s3', 
                                   aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                                   aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        if ('json' not in file_name):            
            extra_args = {'ACL': 'public-read'}
        else:
            extra_args = None
        local_s3_obj.upload_file(file_name,
                                self.s3_bucket,
                                obj_name_s3,
                                ExtraArgs=extra_args
                                )
    
    @timed(1)                         
    def read_history(self):
        '''
            Wrapper function to obtain default history or history from S3
        '''
        self.history_json = self.__get_history__()        
        return self.history_json
    
    def get_bucket_url(self):
        bucket_url = f"https://{self.s3_bucket}.s3.{os.environ.get('AWS_DEFAULT_REGION')}.amazonaws.com"
        print(bucket_url)
        return bucket_url

    def write_history(self, history_list):
        '''
            Writes latest history content to S3
            For now we will assume that the application and S3 have same copy.
        '''
        print("Before update",len(self.history_json))
        if len(history_list) > 0:
            self.history_json.extend(history_list)
        else:
            print("No updates to be made for history")
        print("After update",len(self.history_json))
        history_filename = os.path.join('./static/text', self.history_file)

        with open(history_filename, 'a') as f:
            for entry in history_list:
                f.write(json.dumps(entry) + "\n")
        # for entry in history_list:
        #     self.upload_to_s3(entry['path'], 
        #                         os.path.join(entry['id'], 
        #                                     os.path.basename(entry['path'])
        #                                     )
        #                     )
        # self.upload_to_s3(history_filename, self.history_file)

        upload_list = [ {entry['path']: os.path.join(entry['id'], 
                                            os.path.basename(entry['path'])
                                            ) } for entry in history_list 
                      ]
        upload_list.append({history_filename: self.history_file})

        for entry in upload_list:
            k,v = list(*entry.items())
            t = threading.Thread(target = self.upload_to_s3, args=(k,v)).start()

    def __check_s3_content(self, objname):
        '''
            Returns whether a given objname in present in S3 bucket
        '''
        try:
            s3_contents = self.s3_obj.list_objects_v2(Bucket="emlopsbucket")
            if s3_contents['KeyCount'] < 1:
                print(f'Key {objname} not found in current bucket')
                return False                

            for elem in s3_contents['Contents']:
                if (objname == elem['Key']):
                    return True
            
            print(f'Key {objname} not found in current bucket')
            return False

        except Exception as e:
            print("Unable to fetch S3 details", e)
            return False          

    def __get_history__(self):
        '''
            Retrieve or create base history file
        '''
        history_json = []
        ### First check if the file already exists
        local_file_name = os.path.join('./static/text', self.history_file)
        if (os.path.isfile(local_file_name)):
            with open(local_file_name, 'r') as f:
                for entry in f:
                    history_json.append(json.loads(entry))
            return history_json
        
        ### Confirm if S3 also doesn't have history file
        if (self.__check_s3_content(self.history_file) == False):
            print("Bucket not initialized")
            return self.__create_base_history__()
        
        out_json = self.s3_obj.get_object(Bucket=self.s3_bucket, 
                                          Key=self.history_file
                                          )
        bytestream = out_json['Body'].read()
        for i in bytestream.decode('utf-8').split('\n'):
            if(i != ''):
               history_json.append(json.loads(i))
        print("Downloaded history file from bucket:",history_json)
        return history_json
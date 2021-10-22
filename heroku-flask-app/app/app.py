from flask import Flask, render_template, request, send_from_directory
from models import MobileNet
import os
from math import floor
from utils import rand_run_name
from aws import S3Handler
import argparse

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
model = MobileNet()
s3_bucket_handler = S3Handler()
default_props = []

@app.route('/')
def index():
    return render_template('index.html', items=default_props)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/uploads/<path:path>')
def send_js(path):
    # print(path)
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

@app.route('/history')
def send_history():
    local_history_list = s3_bucket_handler.read_history()
    
    base_s3_url = s3_bucket_handler.get_bucket_url()
    if len(local_history_list) > 5:
        local_history_list = local_history_list[-5:]

    for elem in local_history_list:
        elem['path'] = "/".join([base_s3_url, elem['id'], os.path.basename(elem['path'])])
    return render_template('history.html', items=local_history_list)

@app.route('/infer', methods=['POST'])
def success():
    if request.method == 'POST':
        
        # f = request.files['file']
        print(request.data, request.files.getlist('file'))
        file_list = request.files.getlist('file')
        # inference_arr = list()
        # confidence_arr = list()
        local_id = rand_run_name()
        final_list = list()
        try:
            for f in file_list:        
                saveLocation = os.path.join('./uploads/imgs', f.filename)
                f.save(saveLocation)
                print(saveLocation)
                inference, confidence = model.infer(saveLocation)
                # make a percentage with 2 decimal points
                confidence = floor(confidence * 10000) / 100
                final_list.append({"id":local_id,
                                "path":saveLocation, 
                                "class":inference, 
                                "confidence":confidence})

                # delete file after making an inference
                # os.remove(saveLocation)
            # respond with the inference
            # return render_template('inference.html', name=inference_arr, confidence=confidence_arr)
            # final_list = list(zip(file_list, inference_arr, confidence_arr))
            print(final_list)        
            ### Invoke saving to S3 before returning
            s3_bucket_handler.write_history(final_list)
        
        except Exception as e:
            print("Some exception during ")
            return render_template('error.html')

        return render_template('inference.html', items=final_list)

def set_default_props(filename):
    file_location = os.path.join('./static/saved_imgs',filename)
    if not os.path.isfile(file_location):
        return
    inference, confidence = model.infer(file_location)
    # make a percentage with 2 decimal points
    local_id = 'base'
    confidence = floor(confidence * 10000) / 100
    default_props.append({"id":local_id,
                        "path":file_location, 
                        "class":inference, 
                        "confidence":confidence})

if __name__ == '__main__':
    print("Hello args")
    parser = argparse.ArgumentParser(description = 'Train CIFAR')
    #parser.add_argument("-h", "--help", required=False, help="Can be used to manipulate load-balancing")
    parser.add_argument("-f", "--filename", required=False, help="specify the default filename for inferencing")
    args = parser.parse_args()
    filename = 'static_cover3.jpg'
    print(args)
    if args.filename:
        filename = args.filename
    set_default_props(filename)

    app.debug = True
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port, debug=True)

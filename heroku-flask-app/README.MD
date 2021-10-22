# HEROKU FLASK APP

This repo contains code for deploying a MobileNetV2 model pre-trained on Imagenet dataset on to Heroku as a container.

The code has been tested on WSL2/Linux based machines. For Windows/MacOS you might need additional modifications

### Pre-requisites:

1. Python 3.7 or later installed with dependencies listed in requirements.txt
2. A working docker environment.
3. Valid Heroku account and heroku CLI installed
4. AWS account and a pre-configured S3 bucket.

### Deploying on local system

 Please make sure you have a valid Python(3.7+) installed on your system.

1. Install `virtualenv`:

   ```
   pip3 install virtualenv
   ```

2. Create a Python virtual environment:

   ```
   virtualenv venv
   ```

3. Activate virtual environment:

   1. Linux / WSL2:

   ```
   source venv/bin/activate
   ```

4. Install dependencies:

   ```
   pip3 install -r requirements.txt
   ```

### Run the code

- Make sure you have set the following environment variables before proceeding forward

  ``` 
  export AWS_ACCESS_KEY_ID=<your AWS_ACCESS_KEY_ID>
  export AWS_SECRET_ACCESS_KEY=<your AWS_SECRET_ACCESS_KEY>
  export AWS_DEFAULT_REGION=<your AWS_DEFAULT_REGION>
  export AWS_DEFAULT_REGION=<your AWS_DEFAULT_REGION>
  ```

  

- Run the app (this uses default port as 5000):

  ```
  flask run
  ```

- Run on a specific port:

  ```
  flask run -p <port>
  ```

You should be able to access the webpage on http://localhost:<port>/

### Deploying using Docker on local system

1. The [DockerFile](https://github.com/rajy4683/MLOPs/blob/master/heroku-flask-app/Dockerfile) provided in this repo uses multi-stage builds with base image as python:3.8.5-slim-buster

2. Populate your AWS credentials in the file ``awsenv``

3. Create a Docker image

   ```
   docker build -t pytorchflask -f DockerFile_aws .
   ```

   This will create an image with the name `pytorchflask`. You can replace that with a custom name for your app.

4. Run the docker image with the awsenv file as the input.

   ```
   docker run -d --env-file=awsenv -p 127.0.0.1:5000:80 pytorchflask
   ```

### Deploying to Heroku

1. Make sure you have a working heroku account and heroku CLI installed. Please refer to [this link](https://devcenter.heroku.com/articles/heroku-cli) for more details.

2.  Login to Heroku using CLI

   ``` 
   heroku login
   ```

   

3. Create a new Heroku app. This also provides the URL to be used for your app post deployment (E.g: https://<my-app>.herokuapp.com/)

   ```
   heroku create <my-app>
   ```

   

4. Set the stack for heroku container. This step ensures that heroku builds using container environment from heroku.yml

   ```  
   heroku stack:set container  --app <my-app>
   ```

   

5. Set AWS credentials using heroku set

   ```
   heroku config:set AWS_ACCESS_KEY_ID=<access_key_id> \
   AWS_SECRET_ACCESS_KEY=<aws_secret_access_key> \
   AWS_DEFAULT_REGION=<aws_default_region> \
   S3_DEFAULT_BUCKET=<aws_bucket_name> -a <my-app>
   ```

   

6. Make sure that git remote points to the heroku app created in Step 3:

   ``` 
   git remote -v
   heroku  https://git.heroku.com/<my-app>.git (fetch)
   heroku  https://git.heroku.com/<my-app>.git (push)
   ```

   

7. Add and commit the files to heroku using git commands. 

   ```
   git add .
   git commit -m "Commit details"
   ```

   

8. Push the final changes to heroku. This should trigger docker image build and deployment.

   ```
   git push heroku master
   ```

9. Once the app is deployed to heroku you can check the details using:

   ``` 
   heroku apps
   heroku ps -a <my-app>
   
   #### For logs of delployment and the app
   heroku logs -a <my-app>
   ```

   

10. You can now access the deployed app using the URL from Step 3 i.e https://<my-app>.herokuapp.com/


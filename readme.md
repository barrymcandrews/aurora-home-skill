# Aurora Home Skill

This project is an Alexa Home Skill that allows a person to control LED RGB strips connected with Aurora Server. For more information on Aurora Server see the full project [here](https://github.com/barrymcandrews/aurora-server).  

## Using This Project

First follow [Amazon's instructions](https://github.com/alexa/alexa-smarthome/wiki/Build-a-Working-Smart-Home-Skill-in-15-Minutes) to set up an Alexa home skill. Once you have a skill registered, clone the project into a directory on your computer. 

For this project to work your Aurora Server must be publicly accessible to the internet and AWS Lambda. In the file `api.py` change the variable `API_URL` to match the public URL of your Aurora Server. 

Once this change is complete place the project directory into a zip file and upload it to AWS Lambda.

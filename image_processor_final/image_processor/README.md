# Steps to setup the image_processor

# Git clone the image_processor repo.
git clone https://github.com/ChintanModi23/charting

# Create a folder where you can keep your all virtual environments for all projects
mkdir ~/virt

# Now create a virtual environment for image_processor with python3.7
virtualenv ~/virt/image_processor -p python3.7

# Once it's crated now we have to activate it & install all requirements to run this project.

To activate
cd image_processor
source bin/activate

after that
pip install -r ~/image_processor/requirements.txt
pip install xlrd
pip install xlwt
pip install xlutils

###### -------------------
modify postgres details in create_connectionpool() method in processor/static/data/import.py as well as processor/controllers/home.py
cd processor/static/data
python import.py 

if table has data run `truncate table image_index;` before python import.py 


Feedback request

POST /feedback HTTP/1.1
Host: 0.0.0.0:2525
Content-Type: multipart/form-data;
Content-Disposition: form-data; name="easy_to_understand"
Content-Disposition: form-data; name="rating"
Content-Disposition: form-data; name="image_key"

###### -------------------

# Now all you have to do is run the start_app.sh to start the image_processor app
cd ~/image_processor; ./start_app.sh

# Now open a browser and enter the below link to access our project.
http://localhost:2525/

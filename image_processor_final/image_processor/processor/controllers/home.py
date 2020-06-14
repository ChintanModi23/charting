from flask import render_template, current_app as app, url_for
import os
from flask import request
import json
import psycopg2
from psycopg2 import pool
import flask_excel as excel
import xlsxwriter
from flask import send_from_directory
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, jsonify
import tensorflow as tf
import numpy as np
from tensorflow.keras import backend
from tensorflow.keras.models import load_model
from keras.applications.resnet50 import ResNet50, preprocess_input
from keras.preprocessing.image import ImageDataGenerator, image
from PIL import Image
from keras.preprocessing.image import load_img
#from keras.models import load_model


threaded_postgreSQL_pool = None

@app.before_first_request
def load_model_to_app():
    app.predictor = load_model('processor/static/model/model.h5')

@app.route('/', methods=['get', 'post'])
def home():
    if request.method == 'POST':
        data = request.form
        chart_type = data.get("chartType")
        #second_chart_type = data.get("secondChartType")
        #pdf = data.get("PDF")
        #year = data.get("Year")
        filter_images = get_image_filter_data(
            chart_type=chart_type
            #second_chart_type=second_chart_type,
            #pdf=pdf,
            #year=year
        )
        return json.dumps(filter_images)
        # return render_template('index.html', filter_images=filter_images)
    return render_template('index.html')

@app.route('/feedback', methods=['post'])
def feedback():
    if request.method == 'POST':
        data = request.form
        name = data.get("name")
        email = data.get("email")
        #rating = data.get("rating")
        linkert1 = data.get("linkert1")
        linkert2 = data.get("linkert2")
        linkert3 = data.get("linkert3")
        linkert4 = data.get("linkert4")
        image_key = data.get("image_key")
        feedback = data.get("feedback")
        occupation = data.get("occupation")
        global threaded_postgreSQL_pool
        if(threaded_postgreSQL_pool is None):
            create_connectionpool()
        try:
            connection  = threaded_postgreSQL_pool.getconn()
            cursor = connection.cursor()
            sql = "INSERT INTO feedback(image_key,name,email,linkert1,linkert2,linkert3,linkert4,feedback,occupation) VALUES('"+image_key+"','"+name+"','"+email+"','"+linkert1+"','"+linkert2+"','"+linkert3+"','"+linkert4+"','"+feedback+"','"+occupation+"')"
            cursor.execute(sql)
            connection.commit()
            cursor.close()
        except:
            if (threaded_postgreSQL_pool):
                threaded_postgreSQL_pool.closeall
                threaded_postgreSQL_pool = None
            raise
        finally:
            if(threaded_postgreSQL_pool):
                threaded_postgreSQL_pool.putconn(connection)
        return json.dumps({"message":"Successfully saved feedback"})

def get_image_filter_data(chart_type):
    print("Inside Function get_image_filter_data")
    ALL = "all"
    where_sql = ""

    if chart_type != 'All':
        where_sql+=" image_index.chart_type in('"+chart_type+"')"
    else:
        where_sql+=""
    
    """if second_chart_type!= 'All' and where_sql:
        where_sql+=" and image_index.secondary_chart_type in('"+second_chart_type+"')"
    elif second_chart_type == 'All' and where_sql:
        where_sql == where_sql
    elif second_chart_type!= 'All' and not where_sql:
        where_sql+=" image_index.secondary_chart_type in('"+second_chart_type+"')"
    else:
        where_sql+=""
    
    if str(pdf) != "All" and where_sql:
        where_sql+=" and image_index.source_pdf in('"+pdf+"')"
    elif str(pdf) == "All" and where_sql:
        where_sql == where_sql
    elif str(pdf) != "All" and not where_sql:
        where_sql+=" image_index.source_pdf in('"+pdf+"')"
    else:
        where_sql+=""
    
    if str(year)!= "all" and where_sql:
        where_sql+=" and image_index.year in('"+year+"')"
    elif str(year)== "all" and where_sql:
        where_sql == where_sql
    elif str(year)!= "all" and not where_sql:
        where_sql+= " image_index.year in('"+year+"')"
    else:
        where_sql+="" """
        
    data = get_psql_data(where_sql)
    response = list()
    for row in data:
        img_path = url_for('static', filename='data/ImageList/' + str(int(row[0])) + ".png")
        current_file_path = os.path.dirname(__file__)
        verify_img_path = os.path.join(current_file_path, ".." + img_path)
        if os.path.isfile(verify_img_path):
            response.append([row[0], img_path, row[2], row[3], row[4]])
    return response

def get_psql_data(where_sql):
    global threaded_postgreSQL_pool
    if(threaded_postgreSQL_pool is None):
        create_connectionpool()
    try:
        connection  = threaded_postgreSQL_pool.getconn()
        cursor = connection.cursor()
        if where_sql:
            sql = "select * from image_index where "+where_sql+";"
        else:
            sql = "select * from image_index;"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        return data
    except:
        if (threaded_postgreSQL_pool):
            threaded_postgreSQL_pool.closeall
            threaded_postgreSQL_pool = None
        raise
    finally:
        if(threaded_postgreSQL_pool):
            threaded_postgreSQL_pool.putconn(connection)

@app.route('/export', methods=['get', 'post'])
def export():
    if request.method == 'POST':
        data = request.form
        global threaded_postgreSQL_pool
        if(threaded_postgreSQL_pool is None):
            create_connectionpool()
        try:
            filename = 'chart_data.xlsx'
            connection  = threaded_postgreSQL_pool.getconn()
            cursor = connection.cursor()
            sql = "SELECT * FROM image_index"
            cursor.execute(sql)
            result = cursor.fetchall()
            res_columns = ['Image ID' , 'Chart Type', 'Description', 'Caption', 'Prediction']
            workbook = xlsxwriter.Workbook(filename) 
            worksheet = workbook.add_worksheet()
            worksheet.set_column(0, 0, 5)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 3, 70)
            cell_format = workbook.add_format({'bold': True, 'font_color': 'black'})
  
            # Start from the first cell. 
            # Rows and columns are zero indexed. 
            row = 2
            column = 0
            for res_column in res_columns:
                worksheet.write(0, column, res_column, cell_format)
                column += 1

            column = 0
            for item in result:
                worksheet.write(row, column, item[0])
                worksheet.write(row, column+1, item[1])
                worksheet.write(row, column+2, item[2])
                worksheet.write(row, column+3, item[3])
                worksheet.write(row, column+4, item[4])
                row +=1
            workbook.close()
            cursor.close()
            return send_from_directory(os.getcwd(), filename, as_attachment=True)
        except:
            if (threaded_postgreSQL_pool):
                threaded_postgreSQL_pool.closeall
                threaded_postgreSQL_pool = None
            raise
        finally:
            if(threaded_postgreSQL_pool):
                threaded_postgreSQL_pool.putconn(connection)
    return render_template('export.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    if request.method == 'POST':
        file = request.files['file']
        print("=========filename=========",file)
        extension = os.path.splitext(file.filename)[1]
        #f_name = str(uuid.uuid4()) + extension
        f_name = '2300' + extension
        print("========f_name=========",f_name, extension)
        file_path = os.path.join('processor/static/data/uploads/easy', f_name)
        file.save(file_path)
        print("========file_path=========",file_path )
        test_path = 'processor/static/data/uploads/'
        #image = load_img(file_path + '.png', target_size=(224,224))
        #image = np.resize(image, (224, 224, 3))
        #input_arr = tf.keras.preprocessing.image.img_to_array(image)
        #print("=======input_arr1=======",input_arr.shape)
        #input_arr = input_arr.reshape(1, 224, 224, 3)
        #input_arr = np.array([input_arr])  # Convert single image to a batch
        #print("=======input_arr2=======",input_arr.shape)
        #datagen.fit(input_arr)
        #x_train = datagen.flow(input_arr, batch_size=32)
        #input_arr = input_arr.astype('float32')
        #print("=======input_arr3=======",input_arr)
        test_generator = datagen.flow_from_directory(
        test_path, batch_size=32, class_mode='categorical')
        #predicted = model.predict_generator(test_generator)
        predictions = app.predictor.predict_generator(test_generator)
        #print('===========Predictions=========',predictions)
        #print('INFO Predictions: {}'.format(predictions))
        print("=======shape=======",predictions.shape)
        np.set_printoptions(threshold=np.inf)
        #print("============len====",type(predictions),len(predictions))
        #print("============predictions0000000000====",predictions)
        class_ = np.argmax(predictions, axis=1)
        #class_ = np.where(predictions == np.amax(predictions, axis=1))[1][0]
        print("=======249===============",type(predictions[0]), predictions[0].shape, predictions[0][class_])
        print("=========pred========",class_)
        result = ""
        return result
    return render_template('upload.html', pred='Easy')


def create_connectionpool():
    print("Creating connectionpool")
    global threaded_postgreSQL_pool
    host = "127.0.0.1"
    port = "5432"
    username = ""
    password = "123456"
    db = "imageprocessor"
    min_connection = 1
    max_connection = 2
    try:
        threaded_postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(min_connection, max_connection, host=host, port=port, database=db, user=username, password=password)
        if(threaded_postgreSQL_pool):
            print("Connection pool created successfully using ThreadedConnectionPool")
    except (Exception, psycopg2.DatabaseError) as error :
        print ("Error while connecting to PostgreSQL", error)

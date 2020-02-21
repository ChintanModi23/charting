from flask import render_template, current_app as app, url_for
import os
from flask import request
import json
import psycopg2
from psycopg2 import pool
import flask_excel as excel
import xlsxwriter
from flask import send_from_directory

threaded_postgreSQL_pool = None

@app.route('/', methods=['get', 'post'])
def home():
    if request.method == 'POST':
        data = request.form
        chart_type = data.get("chartType")
        second_chart_type = data.get("secondChartType")
        pdf = data.get("PDF")
        year = data.get("Year")
        filter_images = get_image_filter_data(
            chart_type=chart_type,
            second_chart_type=second_chart_type,
            pdf=pdf,
            year=year
        )
        print(len(filter_images))
        return json.dumps(filter_images)
        # return render_template('index.html', filter_images=filter_images)
    return render_template('index.html')

@app.route('/feedback', methods=['post'])
def feedback():
    if request.method == 'POST':
        data = request.form
        print(data)
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

def get_image_filter_data(chart_type, second_chart_type, pdf, year):
    print("Inside Function get_image_filter_data")
    ALL = "all"
    where_sql = ""
    if chart_type.upper() not in [ALL.upper()]:
        where_sql+=" image_index.chart_type in('"+chart_type+"')"
    else:
        where_sql+=" image_index.chart_type in('Scatter Plot','Box and Whiskers','Connected Scatter Plot','Bar Graph','Area Chart')"
    
    if second_chart_type.upper() not in [ALL.upper()]:
        where_sql+=" and image_index.secondary_chart_type in('"+second_chart_type+"')"
    else:
        where_sql+=" and image_index.secondary_chart_type in('Scatter Plot','Box and Whiskers','Connected Scatter Plot','Bar Graph','Area Chart')"
    
    if str(pdf).upper() not in [ALL.upper()]:
        where_sql+=" and image_index.source_pdf in('"+pdf+"')"
    
    if str(year).upper() not in [ALL.upper()]:
        where_sql+=" and image_index.year in('"+year+"')"
        
    data = get_psql_data(where_sql)
    response = list()
    for row in data:
        img_path = url_for('static', filename='data/ImageList/' + str(int(row[0])) + ".png")
        current_file_path = os.path.dirname(__file__)
        verify_img_path = os.path.join(current_file_path, ".." + img_path)
        if os.path.isfile(verify_img_path):
            response.append([row[0], img_path, row[5], row[6]])
    return response

def get_psql_data(where_sql):
    global threaded_postgreSQL_pool
    if(threaded_postgreSQL_pool is None):
        create_connectionpool()
    try:
        connection  = threaded_postgreSQL_pool.getconn()
        cursor = connection.cursor()
        sql = "select * from image_index where "+where_sql+";"
        print(sql)
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
        #print("========",data)
        #print("===========================")
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
            #print("===========",result,os.getcwd())
            res_columns = ['Source PDF' ,'Year' ,'Chart Type' ,'Secondary Chart Type' ,'Description', 'Caption']
            workbook = xlsxwriter.Workbook(filename) 
            worksheet = workbook.add_worksheet()
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(2, 3, 15)
            worksheet.set_column(4, 5, 70)
            cell_format = workbook.add_format({'bold': True, 'font_color': 'black'})
  
            # Start from the first cell. 
            # Rows and columns are zero indexed. 
            row = 2
            column = 0
            for res_column in res_columns:
                worksheet.write(0, column, res_column, cell_format)
                column += 1

            column = 0
            #print("===========",len(result))
            for item in result:
                #print ("result-----")
                worksheet.write(row, column, item[1])
                worksheet.write(row, column+1, item[2])
                worksheet.write(row, column+2, item[3])
                worksheet.write(row, column+3, item[4])
                worksheet.write(row, column+4, item[5])
                worksheet.write(row, column+5, item[6])
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

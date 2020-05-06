import xlrd
import psycopg2
from psycopg2 import pool
import psycopg2.extras

threaded_postgreSQL_pool = None

def main():
    global threaded_postgreSQL_pool
    if(threaded_postgreSQL_pool is None):
        create_connectionpool()
    create_table()
    workbook = xlrd.open_workbook("imageIndex.xlsx")
    sheet = workbook.sheet_by_index(0)
    images = []
    count = 0
    for rowx in range(sheet.nrows):
        cols = sheet.row_values(rowx)
        if(count==0):
            count+=1
            continue
        image = build_data(cols)
        images.append(image)
        count+=1
    try:
        connection  = threaded_postgreSQL_pool.getconn()
        cursor = connection.cursor()
        sql = """INSERT INTO image_index(image_key, chart_type, description, caption, prediction) VALUES %s"""
        template='(%(image_key)s, %(chart_type)s, %(description)s, %(caption)s, %(prediction)s)'
        psycopg2.extras.execute_values(cursor, sql, images, template=template)
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
            threaded_postgreSQL_pool.closeall
            threaded_postgreSQL_pool = None
    #print(f"Processed image count: {len(images)}")

#psql --host=127.0.0.1 --port=5432 --dbname=imageprocessor
def create_connectionpool():
    print("Creating connectionpool")
    global threaded_postgreSQL_pool
    host = "127.0.0.1"
    port = "5432"
    username = ""
    password = "123456"
    db = "imageprocessor"
    min_connection = 1
    max_connection = 1
    try:
        threaded_postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(min_connection, max_connection, host=host, port=port, database=db, user=username, password=password)
        if(threaded_postgreSQL_pool):
            print("Connection pool created successfully using ThreadedConnectionPool")
    except (Exception, psycopg2.DatabaseError) as error :
        print ("Error while connecting to PostgreSQL", error)

def build_data(image_data):
    table_data = {}
    table_data['image_key'] = image_data[0]
    #table_data['source_pdf'] = image_data[1]
    #table_data['year'] = image_data[2]
    table_data['chart_type'] = image_data[1]
    #table_data['secondary_chart_type'] = image_data[4]
    table_data['description'] = image_data[2]
    table_data['caption'] = image_data[3]
    #table_data['image_url'] = image_data[7]
    #table_data['pdf_link'] = image_data[8]
    table_data['prediction'] = image_data[5]
    return table_data

def create_table():
    connection  = threaded_postgreSQL_pool.getconn()
    cursor = connection.cursor()
    table_name = "image_index"
    sql_create_index_table = "CREATE TABLE IF NOT EXISTS "+table_name+" (image_key INT PRIMARY KEY, chart_type TEXT, description TEXT, caption TEXT, prediction TEXT);"
    cursor.execute(sql_create_index_table)
    sql_create_feedback_table = "CREATE TABLE IF NOT EXISTS feedback (feedback_key SERIAL PRIMARY KEY, name TEXT, email TEXT, linkert1 TEXT, linkert2 TEXT, linkert3 TEXT, linkert4 TEXT, feedback TEXT, image_key INT, occupation TEXT);"
    cursor.execute(sql_create_feedback_table)
    connection.commit()
    cursor.close()
    threaded_postgreSQL_pool.putconn(connection)

if __name__ == "__main__":
    main()

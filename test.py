from sqlalchemy import create_engine

engine = create_engine("mssql+pyodbc://localhost/dataMining?driver=SQL+Server+Native+Client+11.0")
engine.connect()
print(1)
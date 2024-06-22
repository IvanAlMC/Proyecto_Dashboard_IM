import pandas as pd

#BackEnd
#Consumir y almacenar en un dataframe el archivo csv

class preprocesamiento:

    def lee_archivo():
        df_emp = pd.read_csv("employees_con_dep.csv", sep=',', encoding="UTF-8")
        return df_emp
    
    def cuenta_job_id(df_emp):
        df_job=df_emp['JOB_ID'].value_counts().nlargest(9)

        df_job=df_job.reset_index()
        df_job.rename(columns={'index':'JOB_ID', }, inplace=True)
        df_job.rename(columns={'count':'Cantidad', }, inplace=True)
        return df_job
    
    def numero_total_empleados(df_emp):
        # Contar el número total de empleados
        total_empleados = len(df_emp)
        return total_empleados
    
    def numero_total_departamentos(df_emp):
        # Contar el número total de departamentos
        total_departamentos = df_emp['DEPARTMENT_ID'].nunique()
        return total_departamentos
    
    def promedio_salario_empleados(df_emp):
        # Calcular el promedio de salario de los empleados
        promedio_salario = df_emp['SALARY'].mean()
        promedio_redondeado = round(promedio_salario, 2)  # Redondear a 2 decimales
        return promedio_redondeado